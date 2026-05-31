import re

with open(r"d:\CODES\SehatSaathiV2Copy\frontend\doctor-dashboard.html", "r", encoding="utf-8") as f:
    content = f.read()

# Replace sidebar links
sidebar_html = """
        <nav class="nav-menu">
            <a href="doctor-dashboard.html" class="nav-item active">📅 My Schedule</a>
            <a href="#" class="nav-item">🗂️ Patient Records Inbox</a>
            <a href="#" class="nav-item">👤 My Profile Settings</a>
            <a href="login.html" class="nav-item" style="color: #fca5a5;" onclick="localStorage.removeItem('access_token'); localStorage.removeItem('user_role');">🚪 Logout</a>
        </nav>
"""
content = re.sub(r'<nav class="nav-menu">.*?</nav>', sidebar_html, content, flags=re.DOTALL)

# Remove the emergency button
content = re.sub(r'<button class="btn-emergency".*?</button>', '', content, flags=re.DOTALL)

# New Main Content
main_content = """
    <main class="main-content">
        <header class="page-header" style="background: linear-gradient(135deg, #1e293b, #334155); padding: 32px 40px; border-radius: 20px; color: white; margin-bottom: 32px; box-shadow: 0 10px 30px rgba(30, 41, 59, 0.2);">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h1 id="greeting-text" style="color: white; margin-bottom: 8px;">Welcome, Dr. <span id="doctor-name-display"></span></h1>
                    <p style="color: #94a3b8; font-size: 15px; margin-bottom: 0;">Here is your schedule and patient inbox for today.</p>
                </div>
                <div style="background: rgba(255,255,255,0.1); padding: 12px 20px; border-radius: 12px; text-align: center;">
                    <div style="font-size: 13px; color: #94a3b8; margin-bottom: 4px;">Status</div>
                    <label style="display: flex; align-items: center; gap: 8px; font-weight: 600; cursor: pointer;">
                        <input type="checkbox" checked style="accent-color: #10b981; width: 18px; height: 18px;"> Available
                    </label>
                </div>
            </div>
        </header>

        <section class="action-grid" style="grid-template-columns: repeat(3, 1fr);">
            <div class="action-card" style="background: #f0fdfa; border-color: #ccfbf1;">
                <div class="icon-box" style="color: #0d9488; background: #ccfbf1;">📅</div>
                <h3 style="font-size: 24px; margin-bottom: 4px;" id="stat-today">0</h3>
                <p>Today's Appointments</p>
            </div>
            <div class="action-card" style="background: #eff6ff; border-color: #dbeafe;">
                <div class="icon-box" style="color: #3b82f6; background: #dbeafe;">📥</div>
                <h3 style="font-size: 24px; margin-bottom: 4px;">2</h3>
                <p>New Patient Records</p>
            </div>
            <div class="action-card" style="background: #fdf4ff; border-color: #fae8ff;">
                <div class="icon-box" style="color: #c026d3; background: #fae8ff;">💼</div>
                <h3 style="font-size: 24px; margin-bottom: 4px;" id="stat-total">0</h3>
                <p>Total Patients</p>
            </div>
        </section>

        <section class="dashboard-bottom" style="display: block;">
            <div class="recent-activity" style="width: 100%;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                    <h3>📋 Your Schedule</h3>
                    <input type="date" id="schedule-date" style="padding: 8px 12px; border: 1px solid #e2e8f0; border-radius: 8px; font-family: 'Inter'; outline: none;">
                </div>
                <div id="appointments-list">
                    <!-- Appointments will be injected here -->
                    <div style="text-align: center; padding: 40px; color: #94a3b8;">Loading schedule...</div>
                </div>
            </div>
        </section>
    </main>
"""
content = re.sub(r'<main class="main-content">.*?</main>', main_content, content, flags=re.DOTALL)

# Replace the script at the bottom to fetch /api/appointments/schedule
script_html = """
    <script src="auth-sidebar.js"></script>
    <script>
        document.addEventListener('DOMContentLoaded', async () => {
            // Set today's date in picker
            document.getElementById('schedule-date').valueAsDate = new Date();
            
            const doctorName = localStorage.getItem('user_name');
            if(doctorName) document.getElementById('doctor-name-display').textContent = doctorName;

            const token = localStorage.getItem('access_token');
            if (!token) {
                window.location.href = 'login.html';
                return;
            }
            if (localStorage.getItem('user_role') !== 'doctor') {
                window.location.href = 'index.html';
                return;
            }

            try {
                const res = await fetch('/api/appointments/schedule', {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (!res.ok) throw new Error("Failed to fetch schedule");
                
                const appts = await res.json();
                
                document.getElementById('stat-total').textContent = appts.length;
                
                // Filter for today
                const todayStr = new Date().toISOString().split('T')[0];
                const todays = appts.filter(a => a.appt_date === todayStr);
                document.getElementById('stat-today').textContent = todays.length;

                const listEl = document.getElementById('appointments-list');
                if (appts.length === 0) {
                    listEl.innerHTML = '<div style="text-align: center; padding: 40px; color: #94a3b8;">No appointments scheduled.</div>';
                    return;
                }

                listEl.innerHTML = '';
                appts.forEach(appt => {
                    const statusColor = appt.status === 'Confirmed' ? '#10b981' : (appt.status === 'Cancelled' ? '#ef4444' : '#64748b');
                    
                    const el = document.createElement('div');
                    el.className = 'activity-item';
                    el.innerHTML = `
                        <div class="act-icon" style="background: #e0e7ff; color: #4f46e5;">👤</div>
                        <div class="act-details" style="flex: 1;">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <strong>Patient Appointment</strong>
                                <span style="font-size: 12px; font-weight: 600; color: ${statusColor}; background: ${statusColor}20; padding: 4px 8px; border-radius: 6px;">${appt.status}</span>
                            </div>
                            <p style="margin-top: 4px;"><strong>Hospital:</strong> ${appt.hospital}</p>
                            <p><strong>Reason:</strong> ${appt.reason || 'Not provided'}</p>
                            <div style="margin-top: 8px; display: flex; gap: 12px;">
                                <button style="padding: 6px 12px; background: white; border: 1px solid #e2e8f0; border-radius: 6px; cursor: pointer; font-size: 13px; font-weight: 500;">📝 Write Consult Note</button>
                                <button style="padding: 6px 12px; background: white; border: 1px solid #e2e8f0; border-radius: 6px; cursor: pointer; font-size: 13px; font-weight: 500; color: #0ea5e9;">🗂️ View Shared Records</button>
                            </div>
                        </div>
                    `;
                    listEl.appendChild(el);
                });
            } catch (err) {
                document.getElementById('appointments-list').innerHTML = `<div style="text-align: center; padding: 40px; color: #ef4444;">Error loading schedule: ${err.message}</div>`;
            }
        });
    </script>
</body>
</html>
"""
content = re.sub(r'<script src="auth-sidebar\.js"></script>.*', script_html, content, flags=re.DOTALL)

with open(r"d:\CODES\SehatSaathiV2Copy\frontend\doctor-dashboard.html", "w", encoding="utf-8") as f:
    f.write(content)
print("Updated doctor-dashboard.html successfully")
