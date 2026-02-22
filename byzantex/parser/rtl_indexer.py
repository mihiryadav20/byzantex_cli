from pathlib import Path
from typing import Dict, List, Optional


class RTLIndexer:
    """Index RTL and DV .sv/.svh files from an OpenTitan checkout."""

    def __init__(self, opentitan_path: str):
        self.opentitan_path = Path(opentitan_path)
        # filename → list of all repo-relative paths (multiple files can share a name)
        self.file_index: Dict[str, List[str]] = {}

    def index_ip(self, ip_name: Optional[str]) -> int:
        """Index files for a specific IP plus shared DV libraries."""
        count = 0
        hw = self.opentitan_path / "hw"

        if ip_name:
            ip_path = hw / "ip" / ip_name
            if ip_path.exists():
                count += self._scan(ip_path)

        # Always include shared DV libraries (cip_lib, dv_utils, etc.)
        dv_path = hw / "dv"
        if dv_path.exists():
            count += self._scan(dv_path)

        return count

    def index_all(self) -> int:
        """Index every .sv/.svh under hw/."""
        hw = self.opentitan_path / "hw"
        return self._scan(hw) if hw.exists() else 0

    def _scan(self, root: Path) -> int:
        count = 0
        for ext in ("*.sv", "*.svh"):
            for f in root.rglob(ext):
                rel = f.relative_to(self.opentitan_path).as_posix()
                self.file_index.setdefault(f.name, []).append(rel)
                count += 1
        return count

    def resolve(self, file_name: str, ip_name: Optional[str] = None) -> Optional[str]:
        """Return the best repo-relative path for a bare filename.

        When multiple paths share the same filename, prefers the one under
        the given IP (e.g. hw/ip/otbn/...) over shared DV libraries.
        """
        matches = self.file_index.get(file_name)
        if not matches:
            return None
        if len(matches) == 1:
            return matches[0]

        if ip_name:
            for m in matches:
                if f"/ip/{ip_name}/" in m:
                    return m

        return matches[0]

    def get_file_type(self, file_name: str, ip_name: Optional[str] = None) -> Optional[str]:
        """Return 'rtl' or 'dv' based on the resolved path, or None."""
        path = self.resolve(file_name, ip_name)
        if not path:
            return None
        if "/rtl/" in path:
            return "rtl"
        if "/dv/" in path:
            return "dv"
        return "unknown"
