# Sehat Saathi 🩺

Sehat Saathi is a powerful, AI-driven digital healthcare platform that bridges the gap between patients and doctors. Built with a modern aesthetic and a high-performance backend, it offers everything from instant AI medical analysis to secure doctor-patient communication and medical record management.

## ✨ Key Features

### For Patients
- **AI Triage & Symptom Checker:** Get immediate, AI-driven guidance on your symptoms before booking a consultation.
- **Medical Records Vault:** Securely upload, store, and manage your medical history, lab reports, and prescriptions.
- **AI Report Analyzer:** Upload complex medical reports and have the AI break them down into simple, easy-to-understand summaries.
- **Smart Diet Planner:** Generate personalized, AI-curated diet and nutrition plans based on your medical profile.
- **Find Doctors & Live Location:** Search for specialists and view their live clinic locations on an interactive map.

### For Doctors
- **Doctor Dashboard:** Manage your profile, consultation fees, and live availability status.
- **Patient Chat & Prescriptions:** Chat directly with patients and issue digital, printable prescriptions instantly.
- **Create Medical Reports:** Directly upload or create lab results and discharge summaries that instantly sync to the patient's personal record vault.

## 🛠️ Tech Stack

- **Backend:** [FastAPI](https://fastapi.tiangolo.com/) (Python) for lightning-fast, asynchronous API handling.
- **Database:** PostgreSQL (Cloud deployment) / SQLite (Local development) via SQLAlchemy ORM.
- **Frontend:** Vanilla HTML, CSS, and JavaScript, styled with a premium dark-mode aesthetic.
- **AI Integration:** Google Gemini API for advanced medical report analysis and generative diet planning.
- **Authentication:** Secure JWT (JSON Web Tokens) with bcrypt password hashing.

## 🚀 Running Locally

1. **Clone the repository**
   ```bash
   git clone https://github.com/Krishnachaudhary17/SehatSaathi.git
   cd SehatSaathi
   ```

2. **Set up the virtual environment**
   ```bash
   cd backend
   python -m venv venv
   .\venv\Scripts\activate  # Windows
   source venv/bin/activate # Mac/Linux
   ```

3. **Install dependencies**
   ```bash
   pip install -r ../requirements.txt
   ```

4. **Set up Environment Variables**
   Create a `.env` file inside the `backend/` directory:
   ```env
   DATABASE_URL="sqlite+aiosqlite:///./database.db"
   SECRET_KEY="your_secure_random_string"
   ALGORITHM="HS256"
   ACCESS_TOKEN_EXPIRE_MINUTES="60"
   GEMINI_API_KEY="your_google_gemini_api_key"
   ```

5. **Start the server**
   ```bash
   uvicorn main:app --reload --port 8000
   ```
   *The app will automatically serve the frontend on `http://localhost:8000/`*

## ☁️ Deploying to Render

This repository is pre-configured for one-click deployment using **Render Blueprints**.

1. Go to [Render Dashboard](https://dashboard.render.com/) and click **New > Blueprint**.
2. Connect this GitHub repository.
3. Render will automatically read the `render.yaml` file, spin up a **PostgreSQL Database**, and build the **Web Service**.
4. In the Render Dashboard, go to the Environment tab for the new Web Service and add your `GEMINI_API_KEY`.
