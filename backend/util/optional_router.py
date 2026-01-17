def include_optional_router(app, import_path: str, prefix: str = "/api"):
    try:
        mod = __import__(import_path, fromlist=["router"])
        app.include_router(mod.router, prefix=prefix)
        return True
    except Exception:
        # import traceback; print(f"[optional_router] {import_path} failed:\n{traceback.format_exc()}")
        return False
