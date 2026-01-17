from abc import ABC, abstractmethod
from typing import Any, Dict


class ProviderAdapter(ABC):
    name: str

    @abstractmethod
    def health(self) -> Dict[str, Any]:
        ...

    @abstractmethod
    def validate_signature(self, body: bytes, signature: str | None) -> bool:
        ...
