import sys
sys.path.insert(0, 'services/api')
from app.services.jarvis_interactions import add_interaction, INTERACTIONS_FILE
print(f'Interactions file: {INTERACTIONS_FILE}')
result = add_interaction(2, 'Sarah Collins', 'sms', 'SMS followup')
print(f'Added interaction ID {result["id"]}')
