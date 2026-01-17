import importlib
m=importlib.import_module('valhalla.services.api.main')
app = getattr(m,'app')
for r in app.routes:
    print(r.path)
