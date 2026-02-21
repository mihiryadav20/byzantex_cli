import re
from typing import List, Optional


class LogParser:
    """Parse UVM simulation logs and extract failures."""

    # Regex patterns
    PATTERNS = {
        # UVM_ERROR @ 3622247063 ps: (file.sv:123) [component] message
        'uvm_error': re.compile(
            r'UVM_(ERROR|FATAL)\s*@\s*([\d\.]+)\s*(\w+):\s*'
            r'\(([^:]+\.svh?[^:]*):(\d+)\)\s*'
            r'\[([^\]]+)\]\s*(.*)'
        ),

        # xmsim: *E,ASRTST (path/file.sv,123): ... Assertion X has failed
        'xcelium_assert': re.compile(
            r'xmsim:\s*\*E,ASRTST\s*\(([^,]+),(\d+)\).*?Assertion\s+([\w\.]+)\s+has\s+failed'
        ),
    }

    def __init__(self, log_content: str):
        self.log_content = log_content
        self.lines = log_content.split('\n')

    def parse(self) -> List[dict]:
        """Parse log and extract all failures."""
        failures = []

        for line in self.lines:
            if not line.strip():
                continue

            failure = self._parse_uvm_error(line)
            if failure:
                failures.append(failure)
                continue

            failure = self._parse_xcelium_assert(line)
            if failure:
                failures.append(failure)

        return failures

    def _parse_uvm_error(self, line: str) -> Optional[dict]:
        """Parse UVM_ERROR or UVM_FATAL line."""
        match = self.PATTERNS['uvm_error'].search(line)
        if match:
            return {
                'error_type': f'UVM_{match.group(1)}',
                'timestamp': f'{match.group(2)} {match.group(3)}',
                'file_path': match.group(4),
                'line_number': int(match.group(5)),
                'component': match.group(6),
                'message': match.group(7).strip(),
                'raw_line': line,
            }
        return None

    def _parse_xcelium_assert(self, line: str) -> Optional[dict]:
        """Parse Xcelium assertion failure."""
        match = self.PATTERNS['xcelium_assert'].search(line)
        if match:
            full_path = match.group(1)
            file_name = full_path.split('/')[-1]
            return {
                'error_type': 'ASSERTION_FAILED',
                'timestamp': self._extract_time(line),
                'file_path': file_name,
                'full_path': full_path,
                'line_number': int(match.group(2)),
                'assertion_name': match.group(3),
                'message': f'Assertion {match.group(3)} has failed',
                'raw_line': line,
            }
        return None

    def _extract_time(self, line: str) -> str:
        """Extract timestamp from line."""
        match = re.search(r'time\s+(\d+)\s*(\w+)', line, re.IGNORECASE)
        if match:
            return f'{match.group(1)} {match.group(2)}'
        return 'unknown'

    def detect_ip(self) -> Optional[str]:
        """Detect IP name from log content."""
        _GENERIC = {'dv', 'sim', 'uvm', 'test', 'base', 'common', 'env'}

        # Chip-level detection takes priority
        if 'chip_env' in self.log_content or 'top_earlgrey' in self.log_content:
            return 'chip'
        if re.search(r'\[SW_LOG\] Test:', self.log_content):
            return 'chip'

        patterns = [
            r'sequencer\.(\w+?)_',
            r'\[(\w+)_MODEL\]',
            r'(\w+)_base_vseq',
            r'ip_(\w+)_[\d\.]+',
            r'hw/ip/(\w+)/',
        ]

        for pattern in patterns:
            match = re.search(pattern, self.log_content, re.IGNORECASE)
            if match:
                ip = match.group(1).lower()
                if ip not in _GENERIC:
                    return ip

        return None
