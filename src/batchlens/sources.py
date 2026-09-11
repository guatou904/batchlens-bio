"""File-like, in-memory uploads; the audit never needs to save raw web inputs."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Upload:
    name: str
    data: bytes

    @property
    def suffix(self) -> str:
        return Path(self.name).suffix

    def read_bytes(self) -> bytes:
        return self.data

    def read_text(self, encoding: str = "utf-8") -> str:
        return self.data.decode(encoding)


Source = Path | Upload
