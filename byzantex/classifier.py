from typing import Tuple


class Classifier:
    """Classify failures as BUG, TEST, or INFRA."""

    @staticmethod
    def classify(file_path: str, message: str) -> Tuple[str, str]:
        """
        Classify failure and provide reasoning.
        Returns (category, reasoning)
        """

        file_lower = file_path.lower()
        message_lower = message.lower()

        # Software test reference in message (.c file)
        if '.c:' in message or '.cc:' in message:
            return ('TEST', 'Software test failed.')

        # CHECK-STATUS-fail pattern
        if 'check-status-fail' in message_lower:
            return ('TEST', 'Software test check failed.')

        # RTL file → BUG
        if '/rtl/' in file_lower:
            return ('BUG', 'RTL file failure. Design bug.')

        # Timeout → INFRA
        if 'timeout' in message_lower or 'timed out' in message_lower:
            return ('INFRA', 'Timeout detected. Simulation infrastructure issue.')

        # Shared DV library → INFRA
        if 'cip_base' in file_lower or 'cip_lib' in file_lower:
            return ('INFRA', 'Shared DV library issue.')

        # UVM report catcher/server → INFRA
        if 'uvm_report' in file_lower:
            return ('INFRA', 'UVM reporting issue. Error threshold or caught exception.')

        # UVM quit count → INFRA
        if 'quit count' in message_lower:
            return ('INFRA', 'Simulation aborted due to error threshold.')

        # Scoreboard → TEST
        if 'scoreboard' in file_lower:
            return ('TEST', 'Scoreboard mismatch. Check DV or RTL.')

        # Testbench → TEST
        if 'tb.sv' in file_lower or '_tb' in file_lower:
            return ('TEST', 'Testbench assertion failed.')

        # DV sequence → TEST
        if '_vseq' in file_lower or '_seq' in file_lower:
            return ('TEST', 'DV sequence check failed.')

        # Model interface → TEST
        if '_model' in file_lower or '_if.sv' in file_lower:
            return ('TEST', 'DV model/interface issue.')

        # SW logger → TEST
        if 'sw_logger' in file_lower:
            return ('TEST', 'Software logging interface issue.')

        # Software test file → TEST
        if file_path.endswith('.c') or file_path.endswith('.cc'):
            return ('TEST', 'Software test failed.')

        # Default
        return ('UNKNOWN', 'Unable to classify. Manual investigation needed.')
