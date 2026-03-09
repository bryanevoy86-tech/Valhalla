from __future__ import annotations

import os
import hashlib
from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class StoredObject:
    storage_key: str
    sha256: str
    size_bytes: int


class LocalContractStorage:
    def __init__(self, root_dir: str):
        self.root = root_dir
        os.makedirs(self.root, exist_ok=True)

    def put_bytes(self, contract_id: str, filename: str, data: bytes) -> StoredObject:
        sha = hashlib.sha256(data).hexdigest()
        safe_name = filename.replace("\\", "_").replace("/", "_")
        storage_key = f"{contract_id}/{sha}_{safe_name}"
        abs_path = os.path.join(self.root, storage_key)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "wb") as f:
            f.write(data)
        return StoredObject(storage_key=storage_key, sha256=sha, size_bytes=len(data))

    def get_bytes(self, storage_key: str) -> bytes:
        abs_path = os.path.join(self.root, storage_key)
        with open(abs_path, "rb") as f:
            return f.read()

    def exists(self, storage_key: str) -> bool:
        return os.path.exists(os.path.join(self.root, storage_key))
