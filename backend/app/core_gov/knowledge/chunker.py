from __future__ import annotations

from typing import List, Dict, Any

def chunk_text(text: str, chunk_chars: int = 900, overlap: int = 120) -> List[Dict[str, Any]]:
    t = (text or "").strip()
    if not t:
        return []
    chunk_chars = int(chunk_chars or 900)
    overlap = int(overlap or 120)
    out = []
    i = 0
    n = len(t)
    idx = 0
    while i < n:
        j = min(n, i + chunk_chars)
        chunk = t[i:j].strip()
        if chunk:
            out.append({"chunk_index": idx, "text": chunk, "start": i, "end": j})
            idx += 1
        if j >= n:
            break
        i = max(0, j - overlap)
    return out
