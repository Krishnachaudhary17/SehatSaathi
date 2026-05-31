import re

# Read original rehab.html
with open('frontend/rehab.html', 'r', encoding='utf-8') as f:
    rehab_content = f.read()

# Read physio-tracker.html
with open('physiotherapy-exercise-feedback/public/physio-tracker.html', 'r', encoding='utf-8') as f:
    physio_content = f.read()

# Extract styles from physio-tracker.html
styles_match = re.search(r'<style>(.*?)</style>', physio_content, re.DOTALL)
physio_styles = styles_match.group(1) if styles_match else ''

# Namespace physio_styles to not break the sidebar
# We'll wrap the injected physio UI in a div with class "physio-app"
# This might be complex with regex, let's just prepend .physio-app to major selectors, or 
# since SehatSaathi sidebar is strictly styled, we can just dump the styles in and hope they don't clash too much.
# Wait, physio-tracker redefines :root. I will replace :root with .physio-app.
# Also it resets * { ... }. I will remove the reset.
physio_styles = re.sub(r':root\s*\{', '.physio-app {', physio_styles)
physio_styles = re.sub(r'\*,\s*\*\:\:before,\s*\*\:\:after\s*\{[^}]*\}', '', physio_styles)
physio_styles = re.sub(r'html\s*\{[^}]*\}', '', physio_styles)
physio_styles = re.sub(r'body\s*\{([^}]*)\}', r'.physio-app {\1}', physio_styles)

# Extract main grid from physio-tracker
main_match = re.search(r'<main class="main-grid">(.*?)</main>', physio_content, re.DOTALL)
physio_ui = main_match.group(1) if main_match else ''

# Extract hidden canvas
canvas_match = re.search(r'<!-- hidden canvas for frame capture -->(.*?)<!--', physio_content, re.DOTALL)
hidden_canvas = canvas_match.group(1).strip() if canvas_match else '<canvas id="capture-canvas" style="display:none;"></canvas>'

# Extract script
script_match = re.search(r'<script>(.*?)</script>\s*</body>', physio_content, re.DOTALL)
physio_script = script_match.group(1) if script_match else ''

# We need to change the API endpoint in the script from standalone to integrated.
# Original: let backendUrl    = localStorage.getItem('physio_backend') || 'http://localhost:8000';
physio_script = physio_script.replace(
    "let backendUrl    = localStorage.getItem('physio_backend') || 'http://localhost:8000';",
    "let backendUrl    = '/api/rehab';"
)
physio_script = physio_script.replace(
    "document.getElementById('backend-url-input').value = backendUrl;",
    "// removed"
)

# Now, split rehab_content at <main class="main-content">
parts = rehab_content.split('<main class="main-content">')
top_part = parts[0]
bottom_part = parts[1]

# Find the end of <main class="main-content">
# It ends right before <!-- ===== NOTIFICATIONS / SCRIPTS ===== --> or <script>
main_end_idx = bottom_part.find('</main>')

new_main_content = f"""
    <main class="main-content" style="padding: 24px; background: #0a0d12;">
        <style>
        {physio_styles}
        
        /* Overrides to ensure it fits well inside the main-content */
        .physio-app .main-grid {{
            padding: 0;
            max-width: 100%;
        }}
        </style>

        <div class="physio-app">
            <header class="app-header" style="margin-bottom: 20px; border-radius: 12px;">
              <div class="logo">
                <div class="logo-icon">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                    <path d="M4.5 12.5c0-4.142 3.358-7.5 7.5-7.5s7.5 3.358 7.5 7.5"/>
                    <circle cx="12" cy="15" r="3"/>
                    <path d="M12 12V8"/>
                  </svg>
                </div>
                PhysioAI Rehab Monitor
              </div>
              <div class="header-status">
                <div class="status-dot" id="status-dot"></div>
                <span id="status-text">Camera off</span>
              </div>
            </header>

            <div class="main-grid">
                {physio_ui}
            </div>
            {hidden_canvas}
        </div>
    </main>
"""

new_bottom = bottom_part[main_end_idx + 7:]

# Insert the script before </body>
script_insert = f"""
    <script>
    {physio_script}
    </script>
"""
new_bottom = new_bottom.replace('</body>', script_insert + '</body>')

new_html = top_part + new_main_content + new_bottom

with open('frontend/rehab_new.html', 'w', encoding='utf-8') as f:
    f.write(new_html)

print("Successfully merged into frontend/rehab_new.html")
