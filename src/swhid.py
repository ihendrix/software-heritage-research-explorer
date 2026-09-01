from __future__ import annotations

from dataclasses import dataclass
import re
from urllib.parse import quote

SWHID_RE = re.compile(
    r"^swh:(?P<version>\d+):(?P<type>cnt|dir|rev|rel|snp):(?P<id>[0-9a-fA-F]{40})(?P<qualifiers>(?:;.*)?)$"
)
TYPE_NAMES = {
    "cnt": "content",
    "dir": "directory",
    "rev": "revision",
    "rel": "release",
    "snp": "snapshot",
}


@dataclass(frozen=True)
class ParsedSWHID:
    raw: str
    version: int
    object_type: str
    object_id: str
    qualifiers: str

    @property
    def table(self) -> str:
        return TYPE_NAMES[self.object_type]

    @property
    def core(self) -> str:
        return f"swh:{self.version}:{self.object_type}:{self.object_id}"

    @property
    def archive_url(self) -> str:
        return "https://archive.softwareheritage.org/" + quote(self.raw, safe=":;/=%")


def parse_swhid(value: str) -> ParsedSWHID:
    cleaned = value.strip()
    match = SWHID_RE.match(cleaned)
    if not match:
        raise ValueError("Expected a core SWHID such as swh:1:rev:<40 hex characters>.")
    version = int(match.group("version"))
    if version != 1:
        raise ValueError("This explorer currently supports SWHID scheme version 1.")
    return ParsedSWHID(
        raw=cleaned,
        version=version,
        object_type=match.group("type").lower(),
        object_id=match.group("id").lower(),
        qualifiers=match.group("qualifiers") or "",
    )
