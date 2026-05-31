"""
PhysioAI — FastAPI Backend
==========================
Receives base64-encoded webcam frames + exercise context from the browser,
sends them to Google Gemini 1.5 Flash (vision model) for biomechanical analysis,
and returns a structured JSON feedback object that the frontend can speak aloud.

Endpoints
---------
POST /analyze   – analyse a single frame
GET  /exercises – list available exercise profiles
GET  /health    – liveness probe

Run
---
    pip install -r requirements.txt
    GEMINI_API_KEY=your_key uvicorn main:app --reload --port 8000

CORS is wide-open for local development.  Tighten origins before deploying.
"""

import base64
import io
import os
import textwrap
import time
from typing import Optional

import google.generativeai as genai
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
from pydantic import BaseModel

load_dotenv()

# ---------------------------------------------------------------------------
# Gemini setup
# ---------------------------------------------------------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

MODEL_NAME = "gemini-1.5-flash"          # vision-capable, fast & cheap

# ---------------------------------------------------------------------------
# Exercise profiles
# Each profile gives Gemini precise clinical guidance so it can reason about
# what "correct" form looks like for that specific exercise.
# ---------------------------------------------------------------------------
EXERCISE_PROFILES: dict[str, dict] = {
    "straight_leg_raise": {
        "name": "Straight Leg Raise",
        "target": "Quadriceps strengthening post ACL / knee replacement",
        "description": "Patient lies flat, lifts the operated leg to ~45°, holds 3 s, lowers.",
        "key_checkpoints": [
            "Leg must be fully straight (knee locked)",
            "Lift to approximately 45 degrees — not too high, not too low",
            "Opposite leg should remain flat and relaxed",
            "Core/back flat against the surface — no arch",
            "Movement should be slow and controlled",
        ],
        "common_errors": [
            "Bending the knee during the raise",
            "Lifting too fast / dropping the leg",
            "Tilting the pelvis / arching the lower back",
            "Leg angle too shallow (< 20°) or too steep (> 60°)",
        ],
    },
    "heel_slide": {
        "name": "Heel Slide",
        "target": "Knee flexion ROM restoration post surgery",
        "description": "Patient slides heel toward buttocks, bending the knee, then returns.",
        "key_checkpoints": [
            "Heel stays in contact with surface throughout",
            "Knee bends progressively — aim for 90° or as prescribed",
            "Movement should be slow, smooth and pain-controlled",
            "Hip should not rotate outward",
        ],
        "common_errors": [
            "Lifting heel off the surface",
            "Rotating hip externally",
            "Jerky or rapid movement",
            "Not reaching target ROM",
        ],
    },
    "terminal_knee_extension": {
        "name": "Terminal Knee Extension (TKE)",
        "target": "Final degrees of knee extension, VMO activation",
        "description": "Standing with resistance band behind knee. Patient straightens knee from ~30° flex to full extension.",
        "key_checkpoints": [
            "Full knee extension achieved at peak contraction",
            "Hip stays neutral — no trunk lean",
            "Slow controlled return (eccentric phase)",
            "Weight evenly distributed or on operative leg as prescribed",
        ],
        "common_errors": [
            "Hyperextending the knee",
            "Trunk leaning forward",
            "Too fast return — missing the eccentric phase",
            "Foot rotating outward",
        ],
    },
    "wall_slide": {
        "name": "Wall Slide (Mini Squat)",
        "target": "Quad + glute strengthening, controlled knee loading",
        "description": "Patient stands with back against wall, slides down to 30-45° knee bend, holds, slides back up.",
        "key_checkpoints": [
            "Knees track over second toe — no valgus collapse",
            "Back stays flat against the wall",
            "Bend only to prescribed depth (30-45°)",
            "Even weight distribution on both feet",
        ],
        "common_errors": [
            "Knee caving inward (valgus)",
            "Sliding too deep (> 60°)",
            "Back leaving the wall",
            "Rising up on toes",
        ],
    },
    "clamshell": {
        "name": "Clamshell",
        "target": "Hip abductor / glute medius strengthening",
        "description": "Side-lying with knees bent. Patient opens top knee like a clamshell while feet stay together.",
        "key_checkpoints": [
            "Feet stay stacked together throughout",
            "Pelvis does not rotate backward",
            "Open knee to ~45° (hip external rotation)",
            "Movement slow and controlled — no momentum",
        ],
        "common_errors": [
            "Rolling pelvis backward to get extra range",
            "Feet separating",
            "Opening too fast",
            "Insufficient range — knee barely lifts",
        ],
    },
    "sitting_posture": {
        "name": "Sitting Posture Assessment",
        "target": "Post-surgical spinal / hip posture rehabilitation and daily habit correction",
        "description": (
            "Patient sits on a chair facing the camera. "
            "The AI assesses static sitting posture across the head, neck, shoulders, "
            "thoracic spine, lumbar spine, hips, and feet positioning."
        ),
        "key_checkpoints": [
            "Head neutral — ears aligned over shoulders, chin not jutting forward",
            "Cervical spine (neck) upright — no forward head posture",
            "Shoulders level and relaxed — not elevated, rounded, or asymmetric",
            "Thoracic spine erect — no excessive kyphosis (rounding of upper back)",
            "Lumbar spine in neutral curve — slight inward curve, NOT flat or hyper-extended",
            "Hips at approximately 90° — thighs parallel to floor, weight distributed evenly on both sitting bones",
            "Knees at 90° and feet flat on the floor — not dangling or crossed",
            "Core lightly engaged — abdomen not slumped forward",
        ],
        "common_errors": [
            "Forward head posture — head drifting ahead of the shoulder line",
            "Rounded upper back (thoracic kyphosis) — shoulders rolling forward",
            "Slumped lumbar spine — loss of the natural inward curve (posterior pelvic tilt)",
            "Anterior pelvic tilt — excessive arch in the lower back, abdomen pushing forward",
            "Asymmetric weight bearing — leaning to one side, one shoulder higher than the other",
            "Legs crossed or feet not flat — disrupts hip and pelvic alignment",
            "Chin tucked too far down — over-corrected cervical flexion",
            "Shoulders raised toward ears — upper trapezius tension / guarding",
        ],
        "posture_zones": [
            {"id": "head_neck",    "label": "Head & Neck",     "description": "Neutral cervical alignment, ears over shoulders"},
            {"id": "shoulders",    "label": "Shoulders",        "description": "Level, relaxed, not rounded"},
            {"id": "thoracic",     "label": "Upper Back",       "description": "Upright thoracic spine, no kyphosis"},
            {"id": "lumbar",       "label": "Lower Back",       "description": "Natural lumbar curve maintained"},
            {"id": "hips_pelvis",  "label": "Hips & Pelvis",   "description": "90° hip angle, neutral pelvic tilt"},
            {"id": "knees_feet",   "label": "Knees & Feet",    "description": "90° knees, feet flat on floor"},
        ],
    },
}

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------
class AnalyzeRequest(BaseModel):
    frame_base64: str          # data:image/jpeg;base64,<data>  OR plain base64
    exercise_id: str
    rep_count: Optional[int] = 0
    session_duration_s: Optional[float] = 0.0

class FeedbackResponse(BaseModel):
    status: str                # "correct" | "needs_correction" | "error"
    primary_feedback: str      # Short, speakable sentence (spoken aloud by TTS)
    detail: str                # Longer clinical explanation shown in the UI
    score: int                 # 0-100 form quality score
    corrections: list[str]     # Specific things to fix right now
    encouragement: str         # Motivational closing line
    processing_ms: int
    zone_scores: Optional[dict] = None   # populated only for sitting_posture

# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(
    title="PhysioAI",
    description="Real-time orthopaedic physiotherapy exercise analysis via Gemini Vision",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # tighten in production
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Helper: build the Gemini prompt
# ---------------------------------------------------------------------------
def _build_prompt(exercise: dict, rep_count: int, duration: float) -> str:
    checkpoints = "\n".join(f"  • {c}" for c in exercise["key_checkpoints"])
    errors       = "\n".join(f"  • {e}" for e in exercise["common_errors"])

    # ── Sitting posture gets an extended schema with per-zone scoring ──
    if exercise.get("posture_zones"):
        zones = exercise["posture_zones"]
        zone_ids = [z["id"] for z in zones]
        zone_descriptions = "\n".join(
            f'  • {z["id"]} — {z["label"]}: {z["description"]}' for z in zones
        )
        zone_schema = ", ".join(
            f'"{z["id"]}": {{"score": <0-100>, "status": "<ok|warn|poor>", "note": "<brief finding>"}}'
            for z in zones
        )

        return textwrap.dedent(f"""
            You are a highly experienced orthopaedic physiotherapist and ergonomics specialist
            conducting a sitting posture assessment via a webcam frame.

            ASSESSMENT: {exercise['name']}
            PURPOSE:    {exercise['target']}
            DESCRIPTION: {exercise['description']}

            CORRECT POSTURE CHECKPOINTS:
            {checkpoints}

            COMMON POSTURAL ERRORS TO DETECT:
            {errors}

            POSTURE ZONES TO EVALUATE:
            {zone_descriptions}

            SESSION CONTEXT:
            - Time in session: {duration:.0f} seconds

            TASK:
            Carefully analyse the patient's sitting posture across every zone listed above.
            Return ONLY a valid JSON object with this exact schema (no markdown fences, no extra text):

            {{
              "status": "<correct | needs_correction>",
              "primary_feedback": "<one concise spoken sentence ≤ 15 words>",
              "detail": "<2-3 sentence overall posture summary>",
              "score": <integer 0-100 overall posture quality>,
              "corrections": ["<actionable correction 1>", "<actionable correction 2>"],
              "encouragement": "<one motivational sentence>",
              "zone_scores": {{
                {zone_schema}
              }}
            }}

            Rules:
            - zone score 80-100 = ok (green), 50-79 = warn (amber), 0-49 = poor (red)
            - primary_feedback must be the single most important correction to make right now, spoken clearly
            - If the patient is not visible, set status "needs_correction" and primary_feedback "Please sit facing the camera so I can assess your posture."

            Be constructive, specific and encouraging — this patient is in post-surgical rehabilitation.
        """).strip()

    # ── Standard exercise prompt ──
    return textwrap.dedent(f"""
        You are a highly experienced orthopaedic physiotherapist reviewing a patient's
        exercise form via a webcam frame captured at home during post-surgical rehabilitation.

        EXERCISE: {exercise['name']}
        PURPOSE:  {exercise['target']}
        DESCRIPTION: {exercise['description']}

        CORRECT FORM CHECKPOINTS:
        {checkpoints}

        COMMON ERRORS TO WATCH FOR:
        {errors}

        SESSION CONTEXT:
        - Repetitions completed so far: {rep_count}
        - Session duration: {duration:.0f} seconds

        TASK:
        Analyse the image carefully and return ONLY a valid JSON object with this exact schema
        (no markdown fences, no extra text):

        {{
          "status": "<correct | needs_correction>",
          "primary_feedback": "<one concise sentence ≤ 15 words — safe to speak aloud via TTS>",
          "detail": "<2-3 sentence clinical explanation of what you observe>",
          "score": <integer 0-100 representing form quality>,
          "corrections": ["<specific correction 1>", "<specific correction 2>"],
          "encouragement": "<one short motivational sentence>"
        }}

        If the patient is NOT visible or the frame is unclear, set status to "needs_correction"
        and primary_feedback to "Please move into the camera frame so I can see you clearly."

        Be constructive, specific, and encouraging — this patient is recovering from surgery.
    """).strip()


# ---------------------------------------------------------------------------
# Helper: call Gemini
# ---------------------------------------------------------------------------
def _call_gemini(image_bytes: bytes, prompt: str) -> dict:
    if not GEMINI_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="GEMINI_API_KEY is not configured on the server.",
        )

    model = genai.GenerativeModel(MODEL_NAME)

    # Gemini Python SDK accepts PIL images directly
    pil_image = Image.open(io.BytesIO(image_bytes))

    response = model.generate_content([prompt, pil_image])

    raw = response.text.strip()

    # Strip accidental markdown fences Gemini sometimes adds
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    import json
    return json.loads(raw)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/health")
def health():
    return {"status": "ok", "model": MODEL_NAME, "api_key_set": bool(GEMINI_API_KEY)}


@app.get("/exercises")
def list_exercises():
    return [
        {"id": k, "name": v["name"], "target": v["target"]}
        for k, v in EXERCISE_PROFILES.items()
    ]


@app.post("/analyze", response_model=FeedbackResponse)
def analyze_frame(req: AnalyzeRequest):
    t_start = time.monotonic()

    # ------------------------------------------------------------------
    # 1. Decode the frame
    # ------------------------------------------------------------------
    try:
        b64_data = req.frame_base64
        if "," in b64_data:                       # strip data-URL prefix
            b64_data = b64_data.split(",", 1)[1]
        image_bytes = base64.b64decode(b64_data)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid base64 frame: {exc}")

    # ------------------------------------------------------------------
    # 2. Validate exercise id
    # ------------------------------------------------------------------
    exercise = EXERCISE_PROFILES.get(req.exercise_id)
    if not exercise:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown exercise '{req.exercise_id}'. "
                   f"Valid choices: {list(EXERCISE_PROFILES.keys())}",
        )

    # ------------------------------------------------------------------
    # 3. Build prompt and call Gemini
    # ------------------------------------------------------------------
    try:
        prompt  = _build_prompt(exercise, req.rep_count, req.session_duration_s)
        payload = _call_gemini(image_bytes, prompt)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Gemini error: {exc}")

    # ------------------------------------------------------------------
    # 4. Validate / normalise the Gemini response
    # ------------------------------------------------------------------
    processing_ms = int((time.monotonic() - t_start) * 1000)

    return FeedbackResponse(
        status=payload.get("status", "needs_correction"),
        primary_feedback=payload.get("primary_feedback", "Keep going, you're doing great!"),
        detail=payload.get("detail", ""),
        score=max(0, min(100, int(payload.get("score", 70)))),
        corrections=payload.get("corrections", []),
        encouragement=payload.get("encouragement", "You are making great progress!"),
        processing_ms=processing_ms,
        zone_scores=payload.get("zone_scores", None),
    )
