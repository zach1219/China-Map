import json
import urllib.request
import base64
import subprocess

result = subprocess.run(['gh', 'auth', 'token'], capture_output=True, text=True)
TOKEN=result.stdout.strip()
REPO = 'zach1219/China-Map'
HEADERS = {
    'Authorization': f'token {TOKEN}',
    'Accept': 'application/vnd.github.v3+json',
    'Content-Type': 'application/json'
}

BASE_DIR = 'C:/Users/zach/China-Map'

def api_call(url, method='GET', data=None):
    if data:
        data = json.dumps(data).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers=HEADERS, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        print(f"Error {e.code}: {error_body[:300]}")
        return None

def delete_contents(path=''):
    url = f'https://api.github.com/repos/{REPO}/contents/{path}' if path else f'https://api.github.com/repos/{REPO}/contents/'
    contents = api_call(url)
    if not contents:
        return
    if not isinstance(contents, list):
        contents = [contents]
    for item in contents:
        if item['name'] in ['.github']:
            continue
        if item['type'] == 'dir':
            delete_contents(item['path'])
            updated = api_call(f'https://api.github.com/repos/{REPO}/contents/{item["path"]}')
            if updated and not isinstance(updated, list):
                api_call(
                    f'https://api.github.com/repos/{REPO}/contents/{item["path"]}',
                    method='DELETE',
                    data={'message': f'remove {item["name"]}', 'sha': updated['sha']}
                )
                print(f"  Deleted dir: {item['name']}")
        else:
            api_call(
                f'https://api.github.com/repos/{REPO}/contents/{item["path"]}',
                method='DELETE',
                data={'message': f'remove {item["name"]}', 'sha': item['sha']}
            )
            print(f"  Deleted: {item['name']}")

# Step 1: Delete all old files
print("Deleting old files...")
delete_contents()

# Step 2: Create new files
for filename in ['index.html', 'README.md', '.gitignore']:
    print(f"Creating {filename}...")
    with open(f'{BASE_DIR}/{filename}', 'r', encoding='utf-8') as f:
        content = f.read()
    data = {
        'message': f'add {filename}',
        'content': base64.b64encode(content.encode()).decode()
    }
    result = api_call(f'https://api.github.com/repos/{REPO}/contents/{filename}', method='PUT', data=data)
    if result:
        print(f"  Created {filename}")
    else:
        print(f"  Failed to create {filename}")

# Step 3: Rename master to main
print("Checking branches...")
branches = api_call(f'https://api.github.com/repos/{REPO}/branches')
if branches:
    branch_names = [b['name'] for b in branches]
    if 'master' in branch_names and 'main' not in branch_names:
        print("Renaming master to main...")
        result = api_call(
            f'https://api.github.com/repos/{REPO}/branches/master/rename',
            method='POST',
            data={'new_name': 'main'}
        )
        if result:
            print("  Renamed to main")

# Step 4: Update description
print("Updating description...")
api_call(f'https://api.github.com/repos/{REPO}', method='PATCH', data={
    'description': '中国地图数据可视化工具 - 粘贴省份名称自动统计频次着色',
    'homepage': 'https://zach1219.github.io/China-Map/'
})

# Step 5: Enable GitHub Pages
print("Enabling GitHub Pages...")
result = api_call(f'https://api.github.com/repos/{REPO}/pages', method='POST', data={
    'source': {'branch': 'main', 'path': '/'}
})
if result:
    print("  GitHub Pages enabled!")
else:
    result = api_call(f'https://api.github.com/repos/{REPO}/pages', method='PATCH', data={
        'source': {'branch': 'main', 'path': '/'}
    })
    if result:
        print("  GitHub Pages updated!")

print("\nDone! Visit: https://zach1219.github.io/China-Map/")
