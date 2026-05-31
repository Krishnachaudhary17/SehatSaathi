import os
frontend_dir = r'd:\CODES\SehatSaathiV2Copy\frontend'
for f in os.listdir(frontend_dir):
    if f.endswith('.html'):
        p = os.path.join(frontend_dir, f)
        with open(p, 'r', encoding='utf-8') as file:
            c = file.read()
        c = c.replace('<button class="btn-nav-ai" style="margin-top:16px;"', '<button class="btn-nav-ai"')
        with open(p, 'w', encoding='utf-8') as file:
            file.write(c)
print('Done')
