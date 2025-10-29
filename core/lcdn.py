from core.interfaces.i_dnc_agent import IDNCAgent
from core.dnc.dnc_agent import DNCAgent

class LCDN(object):
    """
    This class presents the main LCDN Controller
    """

    def __init__(self):
        # Create all five modules
        self._dnc_agent: IDNCAgent = DNCAgent()


if __name__ == '__main__':
    lcdn = LCDN()
    lcdn._