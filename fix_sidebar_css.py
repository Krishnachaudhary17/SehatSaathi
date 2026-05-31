import os, re

frontend_dir = r'd:\CODES\SehatSaathiV2Copy\frontend'

for filename in os.listdir(frontend_dir):
    if filename.endswith('.html'):
        filepath = os.path.join(frontend_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Add overflow to sidebar
        if 'overflow-y: auto;' not in content:
            content = re.sub(r'(\.sidebar\s*\{[^\}]*)', r'\1\n    overflow-y: auto;\n    overflow-x: hidden;', content)
            
        # Reduce nav-menu margin and gap
        content = re.sub(r'(\.nav-menu\s*\{[^}]*margin-top:\s*)40px', r'\g<1>24px', content)
        content = re.sub(r'(\.nav-menu\s*\{[^}]*gap:\s*)8px', r'\g<1>4px', content)
        
        # Reduce nav-item padding
        content = re.sub(r'(\.nav-item\s*\{[^}]*padding:\s*)12px 16px', r'\g<1>10px 16px', content)
        
        # In case some inline styles use it, we already reduced margin-top inside nav.
        
        # Also let's check for `.sidebar::-webkit-scrollbar` so it looks nice
        if '::-webkit-scrollbar' not in content:
            scrollbar_css = """
.sidebar::-webkit-scrollbar { width: 4px; }
.sidebar::-webkit-scrollbar-track { background: transparent; }
.sidebar::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.2); border-radius: 4px; }
"""
            content = re.sub(r'(</style>)', scrollbar_css + r'\1', content)

        # Let's fix .btn-emergency margin-bottom (in minified css in diet.html and others)
        content = re.sub(r'(\.btn-emergency\s*\{[^}]*margin-bottom:\s*)24px', r'\g<1>12px', content)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
            
print('Updated CSS in all HTML files.')
