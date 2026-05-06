import json
import requests

spec = requests.get('http://127.0.0.1:4000/openapi.json', timeout=5).json()
schema = spec['paths']['/brrrr/deals']['post']['requestBody']['content']['application/json']['schema']
print(json.dumps(schema, indent=2))
