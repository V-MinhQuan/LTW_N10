import glob
import re

faulty = []
for p in glob.glob('QLVB/templates/**/*.html', recursive=True):
    with open(p, 'r', encoding='utf-8') as f:
        content = f.read()
    for line in content.split('\n'):
        if '{% static' in line and '?v=' in line:
            m = re.search(r"{%\s*static\s*['\"][^'\"]*\?v=[^'\"]*['\"]\s*%}", line)
            if m:
                faulty.append((p, line.strip()))

print('Faulty count:', len(faulty))
for f in faulty:
    print(f)

