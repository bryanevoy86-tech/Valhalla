import os

import aiohttp

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")


async def send_slack(text: str, blocks: list | None = None):
    if not SLACK_WEBHOOK_URL:
        return
    payload = {"text": text}
    if blocks:
        payload["blocks"] = blocks
    async with aiohttp.ClientSession() as s:
        await s.post(SLACK_WEBHOOK_URL, json=payload, timeout=15)
