import sys
sys.path.insert(0, 'services/api')
from app.services.jarvis_store import load_contacts
contacts = load_contacts()
print(f'Loaded {len(contacts)} contacts')
