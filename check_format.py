import json
from pathlib import Path

data_dir = Path('data')
json_files = [f for f in data_dir.glob('*.json') if f.name != 'index.json']

required_keys = ['title', 'author', 'genre', 'synopsis', 'cover', 'source_url', 'chapters']
issues = {}
ok_count = 0

for json_file in sorted(json_files):
    try:
        data = json.load(open(json_file, encoding='utf-8'))
        missing = [k for k in required_keys if k not in data]
        
        if missing:
            issues[json_file.name] = missing
        else:
            ok_count += 1
    except Exception as e:
        issues[json_file.name] = [str(e)]

print(f'Total files: {len(json_files)}')
print(f'Format OK: {ok_count}')
print(f'Dengan issue: {len(issues)}')
print()

if issues:
    print('=== Files with issues (first 5) ===')
    for idx, (fname, missing) in enumerate(list(issues.items())[:5]):
        print(f'{idx+1}. {fname}')
        print(f'   Missing: {missing}')
    
    if len(issues) > 5:
        print(f'... dan {len(issues)-5} files lagi')
