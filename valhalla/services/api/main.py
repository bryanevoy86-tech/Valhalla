
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from loguru import logger
import os

APP_NAME = "Valhalla Backend"
VERSION = "v3.0"

app = FastAPI(title=APP_NAME, version=VERSION)

class Command(BaseModel):
    action: str
    payload: dict | None = None

@app.get("/api/health")
def health():
    return {"ok": True, "app": APP_NAME, "version": VERSION}

@app.post("/heimdall/command")
def heimdall_command(cmd: Command):
    logger.info(f"Heimdall received: {cmd.action}")
    # TODO: route to agent skills
    if cmd.action == "ping":
        return {"reply": "pong", "received": cmd.model_dump()}
    return {"reply": "ack", "received": cmd.model_dump()}

@app.post("/builder/deploy")
def builder_deploy():
    # TODO: implement builder pipeline (scaffold pages, connectors, checks)
    token = os.getenv("BUILDER_TOKEN", "")
    if not token:
        raise HTTPException(status_code=401, detail="BUILDER_TOKEN missing")
    return {"status": "queued", "message": "Builder deployment scheduled"}

