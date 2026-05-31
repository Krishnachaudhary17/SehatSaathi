"""
routers/chat.py — AI chat endpoint powered by Google Gemini
Supports: text, images (JPEG/PNG/WebP), PDFs, and Word documents (.docx)
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import base64
import time
import json
import io
from typing import Optional

from schemas import ChatResponse
from utils.model_selector import generate_with_fallback

load_dotenv()

router = APIRouter(prefix="/api/chat", tags=["AI Chat"])

# ── System prompt: conversational Ask AI page ─────────────────────────────────
AI_SYSTEM_PROMPT = """You are Sehat Saathi AI, a friendly and knowledgeable health assistant for users in India, primarily in Ghaziabad, Uttar Pradesh.

You help with:
- Symptom understanding and triage guidance
- General health advice, diet, and lifestyle tips
- Medicine information (generic names, dosage, precautions)
- When to see a doctor vs. home care
- Basic first aid guidance
- Reading and explaining medical reports, prescriptions, or lab results (when a file is shared)

Guidelines:
- Be warm, empathetic, and conversational. Talk like a knowledgeable friend.
- You may respond in Hindi if the user writes in Hindi.
- Always recommend consulting a real doctor for serious concerns.
- NEVER diagnose definitively. Say "this may suggest..." not "you have..."
- Use simple formatting: short paragraphs, plain bullet points with •. Avoid heavy markdown.
- Keep responses under 200 words unless the user needs detailed instructions.
- If a medical emergency, say "Please call 108 immediately."
- If the user shares a document or image of a report/prescription, analyze it and explain it in simple, plain language."""

# ── System prompt: structured Triage page ────────────────────────────────────
TRIAGE_SYSTEM_PROMPT = """You are Sehat Saathi AI, a friendly and calm health assistant for users in India.

Your job:
- Understand symptoms and give a short, clear triage assessment.
- Give practical, helpful next steps.
- Be warm and conversational. Talk like a knowledgeable friend, not a textbook.

Strict formatting rules (VERY IMPORTANT):
- Write in plain, simple sentences. NO markdown. No asterisks, no bullet dashes, no bold text.
- Keep your response under 120 words total. Be concise and to the point.
- Do NOT use headers or sections.
- After your response, on separate lines, add BOTH of these tags:
  SEVERITY:mild OR SEVERITY:moderate OR SEVERITY:severe
  DOCTOR:General Physician (or whatever specialist fits, e.g. Cardiologist, Orthopedic, Dermatologist, ENT, Neurologist, Gastroenterologist, Pulmonologist, Psychiatrist, Gynecologist, Ophthalmologist, Urologist, Endocrinologist, Dentist)
- NEVER use "Call 108" in the response body. Only use SEVERITY:severe if it is truly urgent.

Tone: Calm, friendly, reassuring. Not alarming unless truly necessary."""

# ── System prompt: Medical Report Analyzer (the core feature) ────────────────
REPORT_SYSTEM_PROMPT = """You are a compassionate medical translator. A patient has uploaded a medical report — it could be blood work, an MRI report, a discharge summary, a prescription, or any lab result.

Your ONLY job is to explain this report to a 10-year-old child using simple, everyday words. No jargon. No scary language. Be warm, clear, and reassuring.

You MUST respond in EXACTLY this format with these section headers (do not skip any section):

## PRIMARY_CONDITION
[In 3-8 words, state the primary medical condition, diagnosis, or 'Normal' if healthy.]

## PLAIN_SUMMARY
[Write 3-4 simple sentences that explain what this report is about and what it found overall.]

## KEY_FINDINGS
[List each important finding, one per line, starting with a bullet •. Translate every medical term into plain English.]

## NEXT_STEPS
[List 3-5 clear, practical actions numbered. Be specific about any medicines (include name, dose, timing, duration) and any follow-up appointments (include what, when, which doctor).]

## YOUR_QUESTIONS_ANSWERED
[Write 4-5 questions the patient likely wonders, then answer each in 2 simple sentences. Format:
Q: [question]
A: [answer]]

## SEVERITY_LEVEL
[Write EXACTLY one word: normal OR watch OR concern OR urgent. Then one sentence explaining why.]

IMPORTANT RULES:
- NEVER use medical jargon without immediately explaining it in plain words.
- NEVER say "you have [disease]" — say "this may suggest" or "this could mean".
- If the report looks normal, reassure the patient warmly.
- Always end with encouragement."""


def _build_gemini_history(messages: list) -> list[dict]:
    """Convert message list to Gemini history format."""
    history = []
    for msg in messages:
        role = "model" if msg["role"] == "assistant" else "user"
        history.append({"role": role, "parts": [msg["content"]]})
    return history


def _extract_pdf_text(file_bytes: bytes) -> str:
    """Extract text from a PDF using pypdf."""
    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(file_bytes))
    text_parts = []
    for i, page in enumerate(reader.pages):
        page_text = page.extract_text()
        if page_text:
            text_parts.append(f"[Page {i+1}]\n{page_text.strip()}")
    return "\n\n".join(text_parts)


def _extract_pdf_images(file_bytes: bytes) -> list[dict]:
    """Extract embedded images from a scanned PDF using pypdf.
    Returns a list of inline_data dicts for Gemini (up to 3 pages)."""
    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(file_bytes))
    image_parts = []
    for i, page in enumerate(reader.pages):
        if i >= 3:  # Limit to first 3 pages to stay within token budget
            break
        try:
            for img in page.images:
                image_parts.append({
                    "mime_type": "image/jpeg",
                    "data": img.data,
                })
                break  # One image per page is enough
        except Exception:
            continue
    return image_parts


def _extract_docx_text(file_bytes: bytes) -> str:
    """Extract text from a .docx Word document using python-docx."""
    from docx import Document
    doc = Document(io.BytesIO(file_bytes))
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs) if paragraphs else "[Word document appears to be empty.]"


@router.post("", response_model=ChatResponse)
async def chat(
    messages: str = Form(...),
    image: Optional[UploadFile] = File(default=None),
    mode: str = Form(default="triage"),
):
    if not os.getenv("GEMINI_API_KEY"):
        raise HTTPException(status_code=500, detail="AI service is not configured.")

    try:
        msgs = json.loads(messages)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid messages format.")

    if not msgs:
        raise HTTPException(status_code=400, detail="No messages provided.")

    system_prompt = REPORT_SYSTEM_PROMPT if mode == "report" else (AI_SYSTEM_PROMPT if mode == "chat" else TRIAGE_SYSTEM_PROMPT)
    msgs = msgs[-20:]
    last_msg = msgs[-1]
    if last_msg["role"] != "user":
        raise HTTPException(status_code=400, detail="Last message must be from the user.")

    try:
        history = _build_gemini_history(msgs[:-1])

        # Build message parts
        parts = [last_msg["content"]]

        # Track uploaded file to clean it up from Google's servers afterwards
        uploaded_gemini_file = None

        if image and image.filename:
            file_bytes = await image.read()
            mime = (image.content_type or "").lower()
            filename = image.filename.lower()

            if filename.endswith(".pdf") or mime == "application/pdf":
                extracted_text = _extract_pdf_text(file_bytes)

                if len(extracted_text.strip()) > 100:
                    # ── Text-based PDF: use extracted text ──────────────
                    parts[0] = (
                        f"{last_msg['content']}\n\n"
                        f"[Attached PDF content — please analyze and explain in simple language:]\n\n"
                        f"{extracted_text[:12000]}"
                    )
                else:
                    # ── Scanned / camera PDF: extract embedded images ───
                    img_parts = _extract_pdf_images(file_bytes)
                    if img_parts:
                        # Send text prompt + page images inline
                        parts = [last_msg["content"]] + img_parts
                    else:
                        # Last resort: tell AI it looks like a scan
                        parts[0] = (
                            f"{last_msg['content']}\n\n"
                            "[Note: This PDF appears to be a scanned image. "
                            "Unfortunately no image data could be extracted. "
                            "Please ask the user to upload the document as a JPG or PNG photo instead.]"
                        )

            elif filename.endswith(".docx") or "wordprocessingml" in mime or "openxmlformats" in mime:
                extracted = _extract_docx_text(file_bytes)
                parts[0] = f"{last_msg['content']}\n\n[Attached Word document content below — please analyze and explain this in simple language:]\n\n{extracted}"

            elif mime.startswith("image/") or filename.endswith((".jpg", ".jpeg", ".png", ".webp", ".gif")):
                parts.append({
                    "mime_type": mime if mime.startswith("image/") else "image/jpeg",
                    "data": file_bytes
                })
            else:
                try:
                    text_content = file_bytes.decode("utf-8", errors="ignore")
                    parts[0] = f"{last_msg['content']}\n\n[Attached file content:]\n\n{text_content[:5000]}"
                except Exception:
                    pass

        reply, model_used = generate_with_fallback(
            content=parts,
            system_instruction=system_prompt,
            use_chat=True,
            history=history,
        )
        print(f"\n[DEBUG] Model used: {model_used}\n[DEBUG] Reply preview:\n{reply[:500]}\n")
        return ChatResponse(reply=reply)

    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI error: {str(e)}")


# ── Dedicated endpoint: extract medications & follow-ups from report text ──────
EXTRACT_CARE_PROMPT = """You are a precise medical data extractor. You will be given a medical report analysis text.
Your ONLY job is to extract medicines and follow-up appointments and return them as a JSON object.

Return ONLY this JSON — no explanation, no markdown, no extra text:
{
  "medications": [
    {"name": "medicine name", "dosage": "dose", "timing": "when to take", "duration": "how long", "purpose": "why in simple words"}
  ],
  "followups": [
    {"what": "what to do", "when": "when", "doctor": "which doctor", "note": "extra note"}
  ]
}

Rules:
- If no medicines mentioned, return "medications": []
- If no follow-ups mentioned, return "followups": []
- Extract EVERY medicine and follow-up you can find, even if indirectly mentioned
- Return ONLY the raw JSON object. No ```json``` tags. No explanation."""


class ExtractCareRequest(BaseModel):
    text: str



@router.post("/extract-care")
async def extract_care(req: ExtractCareRequest):
    if not os.getenv("GEMINI_API_KEY"):
        raise HTTPException(status_code=500, detail="AI service not configured.")
    try:
        prompt = f"Extract all medicines and follow-ups from this medical report analysis:\n\n{req.text[:6000]}"
        reply, _ = generate_with_fallback(
            content=[prompt],
            system_instruction=EXTRACT_CARE_PROMPT,
            use_chat=False,
            history=[],
        )
        # Clean up the reply — remove markdown code fences if present
        clean = reply.strip()
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[-1]
        if clean.endswith("```"):
            clean = clean.rsplit("```", 1)[0]
        clean = clean.strip()
        data = json.loads(clean)
        return data
    except json.JSONDecodeError:
        return {"medications": [], "followups": []}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Extraction error: {str(e)}")
