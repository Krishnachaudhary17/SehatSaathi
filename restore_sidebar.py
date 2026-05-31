import os, re

frontend_dir = r'd:\CODES\SehatSaathiV2Copy\frontend'

correct_nav = """        <nav class="nav-menu">
            <a href="index.html" class="nav-item{index_active}">🏠 Home</a>
            <a href="triage.html" class="nav-item{triage_active}">🩺 Triage &amp; Check</a>
            <a href="doctor.html" class="nav-item{doctor_active}">👨‍⚕️ Find Doctor</a>
            <a href="appointments.html" class="nav-item{appts_active}">📅 My Appointments</a>
            <a href="records.html" class="nav-item{records_active}">📄 My Records</a>
            <a href="medicines.html" class="nav-item{meds_active}">💊 Medicine Info</a>
            <a href="rehab.html" class="nav-item{rehab_active}">🏋️ Rehab Monitor</a>
            <a href="report-analyzer.html" class="nav-item{report_active}">🔬 Report Analyzer</a>
            <a href="diet.html" class="nav-item{diet_active}">🥗 Diet Plan</a>
            <button class="btn-nav-ai" onclick="location.href='askai.html'">✨ Ask AI Assistant</button>
        </nav>

        <button class="btn-emergency" onclick="location.href='emergency.html'">
            <span class="alert-icon">⚠️</span> Emergency 108
        </button>"""

nav_pattern = re.compile(r'<nav class="nav-menu">.*?</button>\s*(?=<div class="user-profile)', re.DOTALL)

for filename in os.listdir(frontend_dir):
    if filename.endswith('.html'):
        filepath = os.path.join(frontend_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if '<nav class="nav-menu">' not in content:
            continue
            
        active_flags = {
            'index_active': ' active' if filename == 'index.html' else '',
            'triage_active': ' active' if filename == 'triage.html' else '',
            'doctor_active': ' active' if filename == 'doctor.html' else '',
            'appts_active': ' active' if filename == 'appointments.html' else '',
            'records_active': ' active' if filename == 'records.html' else '',
            'meds_active': ' active' if filename == 'medicines.html' else '',
            'rehab_active': ' active' if filename == 'rehab.html' else '',
            'report_active': ' active' if filename == 'report-analyzer.html' else '',
            'diet_active': ' active' if filename == 'diet.html' else ''
        }
        
        replacement = correct_nav.format(**active_flags)
        new_content = nav_pattern.sub(replacement, content)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f'  Fixed: {filename}')
            
print('Done - all emojis restored!')
