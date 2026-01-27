import json

with open('data/index.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Find entries with 'author' field (newly scraped)
new_ones = [k for k in data.keys() if 'author' in data[k]]
print(f'✓ New scraped entries: {len(new_ones)}')
print(f'✓ Old entries: {len(data) - len(new_ones)}')
print(f'✓ Total: {len(data)}')

print('\nSample of new entries:')
for k in sorted(new_ones)[:3]:
    entry = data[k]
    print(f"  - {k}")
    print(f"    Title: {entry.get('title', 'N/A')}")
    print(f"    Author: {entry.get('author', 'N/A')}")
    print(f"    Chapters: {entry.get('total_chapters', 0)}")
    print(f"    Genre: {entry.get('genre', 'N/A')}")
