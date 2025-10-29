from dataclasses import dataclass
from typing import Optional, Tuple

@dataclass
class Violation:
    """Describes a DNC resource violation."""
    message: str
    edge: Optional[Tuple[int, int]] = None
    used_rate: Optional[float] = None
    max_rate: Optional[float] = None
    current_delay: Optional[float] = None
    max_delay: Optional[float] = None
    used_buffer: Optional[int] = None
    required_buffer: Optional[int] = None
    flow_delay: Optional[float] = None
    flow_deadline: Optional[float] = None

    def __str__(self):
        violation_msg = f'Violation: {self.message} '
        if self.edge:
            violation_msg += f'on edge: {self.edge}. '
        if self.used_rate:
            violation_msg += f'Used rate: {self.used_rate}, Maximum Rate: {self.max_rate}. '
        if self.current_delay:
            violation_msg += f'Current delay: {self.current_delay}, Maximum Delay: {self.max_delay}. '
        if self.used_buffer:
            violation_msg += f'Used buffer: {self.used_buffer}, Maximum Buffer: {self.required_buffer}. '
        if self.flow_delay:
            violation_msg += f'Flow delay: {self.flow_delay}, Flow deadline: {self.flow_deadline}. '

        return violation_msg
