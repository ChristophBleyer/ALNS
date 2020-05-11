class TimeInterval:
    def __init__(self, earliest, latest):
        self._earliest = earliest
        self._latest = latest
    
    @property
    def earliest(self):
        return self._earliest
    
    @property
    def latest(self):
        return self._latest
