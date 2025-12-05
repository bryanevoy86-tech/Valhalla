import importlib.util

test_modules = [
    ('bs4', 'beautifulsoup4'),
    ('cryptography', 'cryptography'),
    ('multipart', 'python-multipart'),
    ('rapidfuzz', 'rapidfuzz'),
    ('reportlab', 'reportlab'),
    ('email_validator', 'email-validator'),
]

for import_name, pkg_name in test_modules:
    spec = importlib.util.find_spec(import_name)
    status = 'INSTALLED' if spec else 'MISSING'
    print(f"{pkg_name:20} ({import_name:15}): {status}")
