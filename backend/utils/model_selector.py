"""
utils/model_selector.py — Shared Gemini model picker with auto-fallback.

Strategy:
  - Try models in PRIORITY_ORDER (best quality first).
  - If a model returns 429 (quota) or 404 (not found), mark it exhausted
    and instantly try the next one — no delay, no retry.
  - Cache the last working model in memory so subsequent requests don't
    re-probe from the top every time.
  - Calling code passes its content + kwargs; this module handles the loop.

Usage in any router:
    from utils.model_selector import generate_with_fallback

    response, model_used = generate_with_fallback(
        content=[prompt, image_part],
        system_instruction="You are ...",
        generation_config=genai.GenerationConfig(max_output_tokens=50),
    )
"""

import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Priority order — best capability first, higher-quota fallbacks last.
# Only models confirmed to work with this API key / SDK version.
PRIORITY_ORDER = [
    "gemini-3.5-flash",        # Latest flash, has quota available
    "gemini-3.1-flash-lite",   # Fast, has quota available
    "gemini-3-flash-preview",  # Preview, has quota available
    "gemini-2.5-flash",        # Excellent, but only 20 req/day on free tier
    "gemini-2.0-flash",        # Good — higher quota on paid, same limit on free
    "gemini-2.0-flash-lite",   # Lightest, highest RPM
    "gemini-2.5-flash-lite",   # Latest lite variant
    "gemini-2.5-flash-preview-05-20",  # Preview variant
]

# Per-process in-memory state (resets when uvicorn restarts)
_exhausted: set[str] = set()
_last_working: str | None = None


def _is_quota_error(e: Exception) -> bool:
    s = str(e)
    return "429" in s or "quota" in s.lower() or "rate limit" in s.lower()


def _is_not_found(e: Exception) -> bool:
    s = str(e)
    return "404" in s or "not found" in s.lower() or "deprecated" in s.lower()


def get_best_model_name() -> str:
    """Return the name of the best currently available model (cached)."""
    global _last_working
    if _last_working and _last_working not in _exhausted:
        return _last_working
    # Pick first non-exhausted from priority list
    for m in PRIORITY_ORDER:
        if m not in _exhausted:
            return m
    # If everything is exhausted, reset and try again (quota may have refreshed)
    _exhausted.clear()
    return PRIORITY_ORDER[0]


def generate_with_fallback(
    content,
    system_instruction: str | None = None,
    generation_config=None,
    use_chat: bool = False,
    history: list | None = None,
) -> tuple:
    """
    Try each model in PRIORITY_ORDER until one succeeds.

    Args:
        content: list of parts (text strings, inline_data dicts) or a single string.
        system_instruction: optional system prompt string.
        generation_config: optional genai.GenerationConfig.
        use_chat: if True, use model.start_chat(history) and send last content part.
        history: list of prior turns for chat mode.

    Returns:
        (response_text: str, model_name_used: str)

    Raises:
        Exception if all models fail for non-quota/non-404 reasons.
    """
    global _last_working, _exhausted

    genai.configure(api_key=GEMINI_API_KEY)

    # Build candidate list: try last working model first for speed
    candidates = []
    if _last_working and _last_working not in _exhausted:
        candidates.append(_last_working)
    for m in PRIORITY_ORDER:
        if m not in candidates and m not in _exhausted:
            candidates.append(m)

    last_error = None

    for model_name in candidates:
        try:
            model = genai.GenerativeModel(
                model_name=model_name,
                system_instruction=system_instruction,
            )

            if use_chat:
                # Chat mode: start session with history, send last content item
                chat_session = model.start_chat(history=history or [])
                response = chat_session.send_message(
                    content,
                    **({"generation_config": generation_config} if generation_config else {})
                )
            else:
                kwargs = {}
                if generation_config:
                    kwargs["generation_config"] = generation_config
                response = model.generate_content(content, **kwargs)

            # ✅ Success — cache and return
            _last_working = model_name
            return response.text.strip(), model_name

        except Exception as e:
            last_error = e
            if _is_quota_error(e) or _is_not_found(e):
                print(f"[ModelSelector] {model_name} unavailable ({type(e).__name__}: {str(e)[:80]}), trying next...")
                _exhausted.add(model_name)
                if _last_working == model_name:
                    _last_working = None
                continue
            else:
                # Unknown error — don't retry, raise immediately
                raise

    # All candidates exhausted
    _exhausted.clear()  # Reset so next request tries fresh (quota may have refreshed)
    raise Exception(
        "Daily API quota exhausted for all available Gemini models. "
        "Free tier allows 20 requests/day per model. "
        "Quota resets at midnight Pacific Time (~12:30 PM IST). "
        f"Last error: {last_error}"
    )
