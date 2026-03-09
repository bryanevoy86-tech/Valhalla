content = 'from app.main import app\n\nprint("[main.py] Delegating to app.main:app")'
with open('services/api/main.py', 'wb') as f:
    f.write(content.encode('utf-8'))
print("✓ File written without BOM")
with open('services/api/main.py', 'rb') as f:
    first_bytes = f.read(4)
    print(f"First bytes: {list(first_bytes)}")
    if first_bytes.startswith(b'\xef\xbb\xbf'):
        print("ERROR: Still has BOM!")
    else:
        print("✓ No BOM detected")
