"""
seed_doctors.py — Populate the database with real-sounding Ghaziabad doctors.
Run once: .\venv\Scripts\python.exe seed_doctors.py
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from database import engine, Base
from models import Doctor
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete

DOCTORS = [
    # ── General Physicians ──────────────────────────
    {
        "name": "Dr. Arvind Sharma",
        "specialty": "General Physician",
        "location": "City Care Hospital, Sector 14, Ghaziabad",
        "lat": 28.6692, "lng": 77.4538,
        "rating": 4.8, "available": True,
        "phone": "9876541001",
        "experience_years": 18, "fee": 500,
        "bio": "Senior GP with 18 years of experience. Expert in fever, infections, and general medicine."
    },
    {
        "name": "Dr. Rohit Verma",
        "specialty": "General Physician",
        "location": "Apollo Hospital, Sector 26, Ghaziabad",
        "lat": 28.6600, "lng": 77.4700,
        "rating": 4.5, "available": False,
        "phone": "9876541002",
        "experience_years": 12, "fee": 400,
        "bio": "General medicine specialist. Known for clear, patient-friendly consultations."
    },
    {
        "name": "Dr. Anita Singh",
        "specialty": "General Physician",
        "location": "Kaushambi Medical Centre, Ghaziabad",
        "lat": 28.6450, "lng": 77.3380,
        "rating": 4.6, "available": True,
        "phone": "9876541003",
        "experience_years": 9, "fee": 350,
        "bio": "Friendly GP specialising in lifestyle diseases, diabetes management, and preventive care."
    },
    # ── Cardiologists ───────────────────────────────
    {
        "name": "Dr. Priya Patel",
        "specialty": "Cardiologist",
        "location": "Heart Institute, MG Road, Ghaziabad",
        "lat": 28.6750, "lng": 77.4600,
        "rating": 4.9, "available": True,
        "phone": "9876541010",
        "experience_years": 22, "fee": 1200,
        "bio": "Interventional cardiologist with expertise in angioplasty and heart failure management."
    },
    {
        "name": "Dr. Manish Gupta",
        "specialty": "Cardiologist",
        "location": "Yashoda Hospital, Kaushambi, Ghaziabad",
        "lat": 28.6480, "lng": 77.3410,
        "rating": 4.7, "available": True,
        "phone": "9876541011",
        "experience_years": 15, "fee": 1000,
        "bio": "Preventive cardiologist. Expert in ECG, Echo, and cardiac risk profiling."
    },
    # ── Pediatricians ───────────────────────────────
    {
        "name": "Dr. Suresh Kumar",
        "specialty": "Pediatrician",
        "location": "Sunshine Kids Clinic, Vaishali, Ghaziabad",
        "lat": 28.6630, "lng": 77.4480,
        "rating": 4.7, "available": True,
        "phone": "9876541020",
        "experience_years": 14, "fee": 600,
        "bio": "Experienced paediatrician. Specialises in newborn care, vaccinations, and child growth."
    },
    {
        "name": "Dr. Kavita Nair",
        "specialty": "Pediatrician",
        "location": "Kids Zone Clinic, Indirapuram, Ghaziabad",
        "lat": 28.6415, "lng": 77.3690,
        "rating": 4.8, "available": False,
        "phone": "9876541021",
        "experience_years": 10, "fee": 550,
        "bio": "Child specialist with a calm, reassuring approach. Expert in childhood allergies and infections."
    },
    # ── Dermatologists ──────────────────────────────
    {
        "name": "Dr. Meera Reddy",
        "specialty": "Dermatologist",
        "location": "Skin & Care Clinic, MG Road, Ghaziabad",
        "lat": 28.6800, "lng": 77.4650,
        "rating": 4.6, "available": True,
        "phone": "9876541030",
        "experience_years": 11, "fee": 800,
        "bio": "Cosmetic and medical dermatologist. Expert in acne, psoriasis, and hair loss treatment."
    },
    {
        "name": "Dr. Ramesh Bhatia",
        "specialty": "Dermatologist",
        "location": "DermaCare Clinic, Raj Nagar, Ghaziabad",
        "lat": 28.6670, "lng": 77.4390,
        "rating": 4.4, "available": True,
        "phone": "9876541031",
        "experience_years": 8, "fee": 700,
        "bio": "Specialises in skin infections, eczema, and laser treatments."
    },
    # ── Orthopedics ─────────────────────────────────
    {
        "name": "Dr. Sanjay Mishra",
        "specialty": "Orthopedic",
        "location": "Bone & Joint Clinic, Vaishali, Ghaziabad",
        "lat": 28.6560, "lng": 77.3500,
        "rating": 4.8, "available": True,
        "phone": "9876541040",
        "experience_years": 20, "fee": 900,
        "bio": "Senior orthopaedic surgeon. Expert in knee replacement, sports injuries, and spine care."
    },
    {
        "name": "Dr. Deepa Agarwal",
        "specialty": "Orthopedic",
        "location": "Max Hospital, Vaishali, Ghaziabad",
        "lat": 28.6380, "lng": 77.3310,
        "rating": 4.6, "available": True,
        "phone": "9876541041",
        "experience_years": 13, "fee": 800,
        "bio": "Expert in joint disorders, fracture management, and post-surgical rehabilitation guidance."
    },
    # ── Neurologists ────────────────────────────────
    {
        "name": "Dr. Vijay Rajan",
        "specialty": "Neurologist",
        "location": "Brain Care Centre, Sector 62, Ghaziabad",
        "lat": 28.6272, "lng": 77.3648,
        "rating": 4.9, "available": True,
        "phone": "9876541050",
        "experience_years": 25, "fee": 1500,
        "bio": "Senior neurologist with expertise in epilepsy, migraines, Parkinson's, and stroke management."
    },
    {
        "name": "Dr. Sunita Chandra",
        "specialty": "Neurologist",
        "location": "Columbia Asia Hospital, Ghaziabad",
        "lat": 28.6340, "lng": 77.3720,
        "rating": 4.7, "available": False,
        "phone": "9876541051",
        "experience_years": 16, "fee": 1200,
        "bio": "Expert in headache disorders, dementia, and neuromuscular diseases."
    },
    # ── ENT ─────────────────────────────────────────
    {
        "name": "Dr. Harish Tiwari",
        "specialty": "ENT",
        "location": "Ear Nose Throat Clinic, Indirapuram",
        "lat": 28.6420, "lng": 77.3700,
        "rating": 4.5, "available": True,
        "phone": "9876541060",
        "experience_years": 11, "fee": 700,
        "bio": "ENT specialist handling sinusitis, hearing loss, tonsillitis, and thyroid issues."
    },
    {
        "name": "Dr. Nalini Joshi",
        "specialty": "ENT",
        "location": "Fortis Hospital, Noida Extn (near GZB border)",
        "lat": 28.6185, "lng": 77.4120,
        "rating": 4.6, "available": True,
        "phone": "9876541061",
        "experience_years": 9, "fee": 650,
        "bio": "Specialises in ear infections, vertigo, and endoscopic nasal surgeries."
    },
    # ── Gastroenterologists ─────────────────────────
    {
        "name": "Dr. Ajay Kulkarni",
        "specialty": "Gastroenterologist",
        "location": "Gut Health Clinic, Raj Nagar Extn, Ghaziabad",
        "lat": 28.6735, "lng": 77.4120,
        "rating": 4.7, "available": True,
        "phone": "9876541070",
        "experience_years": 17, "fee": 1000,
        "bio": "Expert in IBS, Crohn's disease, liver disorders, and endoscopy procedures."
    },
    # ── Gynecologists ───────────────────────────────
    {
        "name": "Dr. Rekha Sharma",
        "specialty": "Gynecologist",
        "location": "Women's Wellness Centre, Vaishali, Ghaziabad",
        "lat": 28.6488, "lng": 77.3468,
        "rating": 4.9, "available": True,
        "phone": "9876541080",
        "experience_years": 19, "fee": 900,
        "bio": "Obstetrician & gynaecologist specialising in high-risk pregnancy, PCOS, and laparoscopy."
    },
    {
        "name": "Dr. Pooja Tiwari",
        "specialty": "Gynecologist",
        "location": "Cloudnine Hospital, Indirapuram, Ghaziabad",
        "lat": 28.6430, "lng": 77.3720,
        "rating": 4.8, "available": True,
        "phone": "9876541081",
        "experience_years": 12, "fee": 800,
        "bio": "Specialises in antenatal care, infertility treatment, and menstrual disorders."
    },
    # ── Pulmonologists ──────────────────────────────
    {
        "name": "Dr. Nitin Saxena",
        "specialty": "Pulmonologist",
        "location": "Breathe Easy Clinic, Sector 14, Ghaziabad",
        "lat": 28.6710, "lng": 77.4520,
        "rating": 4.6, "available": True,
        "phone": "9876541090",
        "experience_years": 14, "fee": 900,
        "bio": "Lung specialist managing asthma, COPD, sleep apnoea, and respiratory infections."
    },
    # ── Endocrinologists ────────────────────────────
    {
        "name": "Dr. Seema Kapoor",
        "specialty": "Endocrinologist",
        "location": "Diabetes & Hormone Clinic, Kaushambi",
        "lat": 28.6460, "lng": 77.3380,
        "rating": 4.7, "available": True,
        "phone": "9876541100",
        "experience_years": 16, "fee": 1100,
        "bio": "Expert in diabetes, thyroid disorders, PCOD, and hormonal imbalances."
    },
    # ── Psychiatrists ───────────────────────────────
    {
        "name": "Dr. Arun Mehta",
        "specialty": "Psychiatrist",
        "location": "Mind Matters Clinic, Indirapuram, Ghaziabad",
        "lat": 28.6405, "lng": 77.3660,
        "rating": 4.8, "available": True,
        "phone": "9876541110",
        "experience_years": 15, "fee": 1200,
        "bio": "Psychiatrist specialising in anxiety, depression, OCD, and addiction management."
    },
    # ── Urologists ──────────────────────────────────
    {
        "name": "Dr. Pankaj Rawat",
        "specialty": "Urologist",
        "location": "Urology Care Centre, MG Road, Ghaziabad",
        "lat": 28.6770, "lng": 77.4620,
        "rating": 4.6, "available": True,
        "phone": "9876541120",
        "experience_years": 13, "fee": 950,
        "bio": "Urologist expert in kidney stones, prostate disorders, UTI, and laparoscopic urology."
    },
    # ── Ophthalmologists ────────────────────────────
    {
        "name": "Dr. Leena Mathur",
        "specialty": "Ophthalmologist",
        "location": "Eye Vision Clinic, Raj Nagar, Ghaziabad",
        "lat": 28.6655, "lng": 77.4370,
        "rating": 4.7, "available": True,
        "phone": "9876541130",
        "experience_years": 10, "fee": 700,
        "bio": "Eye specialist with expertise in cataract surgery, glaucoma, and LASIK consultation."
    },
    # ── Dentists ────────────────────────────────────
    {
        "name": "Dr. Rahul Bhatt",
        "specialty": "Dentist",
        "location": "Smile Dental Studio, Vaishali, Ghaziabad",
        "lat": 28.6490, "lng": 77.3440,
        "rating": 4.8, "available": True,
        "phone": "9876541140",
        "experience_years": 8, "fee": 600,
        "bio": "Cosmetic and general dentist. Expert in dental implants, braces, and root canal treatments."
    },
    {
        "name": "Dr. Sheetal Rana",
        "specialty": "Dentist",
        "location": "BrightSmile Dental Clinic, Indirapuram",
        "lat": 28.6400, "lng": 77.3700,
        "rating": 4.5, "available": False,
        "phone": "9876541141",
        "experience_years": 6, "fee": 500,
        "bio": "Painless dental treatments, teeth whitening, and paediatric dentistry."
    },
    # ── Physiotherapists ────────────────────────────
    {
        "name": "Dr. Kiran Pal",
        "specialty": "Physiotherapist",
        "location": "ActiveLife Physio Centre, Sector 62",
        "lat": 28.6270, "lng": 77.3640,
        "rating": 4.6, "available": True,
        "phone": "9876541150",
        "experience_years": 9, "fee": 500,
        "bio": "Sports physio and rehabilitation expert. Specialises in post-surgery recovery and back pain."
    },
    # ── Dietitians ──────────────────────────────────
    {
        "name": "Ms. Nidhi Agarwal",
        "specialty": "Dietitian",
        "location": "NutriLife Wellness, Kaushambi, Ghaziabad",
        "lat": 28.6470, "lng": 77.3395,
        "rating": 4.9, "available": True,
        "phone": "9876541160",
        "experience_years": 7, "fee": 400,
        "bio": "Clinical dietitian specialising in weight management, diabetes diet, and sports nutrition."
    },
    # ── Oncologists ─────────────────────────────────
    {
        "name": "Dr. Alok Srivastava",
        "specialty": "Oncologist",
        "location": "HCG Cancer Centre, Ghaziabad",
        "lat": 28.6590, "lng": 77.4190,
        "rating": 4.9, "available": True,
        "phone": "9876541170",
        "experience_years": 24, "fee": 2000,
        "bio": "Medical oncologist specialising in chemotherapy, targeted therapy, and cancer survivorship care."
    },
]


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSession(engine) as session:
        # Clear existing doctors first to avoid duplicates on re-run
        await session.execute(delete(Doctor))
        await session.commit()

        for d in DOCTORS:
            session.add(Doctor(**d))

        await session.commit()
        print(f"✅ Seeded {len(DOCTORS)} doctors into the database!")

if __name__ == "__main__":
    asyncio.run(seed())
