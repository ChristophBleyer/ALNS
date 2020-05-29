from .AcceptanceCriterion import AcceptanceCriterion
from .update import update


class ThresholdAcceptance(AcceptanceCriterion):

    def __init__(self, start_threshold, end_threshold, step, method="linear"):
        """
        ``threshold = max(end_threshold, threshold - step)`` (linear)

        ``threshold = max(end_threshold, step * threshold)`` (exponential)

        where the initial threshold is set to ``start_threshold``.

        Parameters
        ----------
        start_threshold : float
            The initial threshold.
        end_threshold : float
            The final threshold.
        step : float
            The updating step.
        method : str
            The updating method, one of {'linear', 'exponential'}. Default
            'linear'.
        """
        if start_threshold < 0 or end_threshold < 0 or step < 0:
            raise ValueError("Thresholds must be positive.")

        if start_threshold < end_threshold:
            raise ValueError("Start threshold must be bigger than end "
                             "threshold.")

        if method == "exponential" and step > 1:
            raise ValueError("For exponential updating, the step parameter "
                             "must not be explosive.")

        self._start_threshold = start_threshold
        self._end_threshold = end_threshold
        self._step = step
        self._method = method

        self._threshold = start_threshold

    @property
    def start_threshold(self):
        return self._start_threshold

    @property
    def end_threshold(self):
        return self._end_threshold

    @property
    def step(self):
        return self._step

    @property
    def method(self):
        return self._method

    def accept(self, rnd, best, current, candidate):
        result = ((candidate.objective() - current.objective()) / candidate.objective()) <= self._threshold

        self._threshold = max(self.end_threshold,
                              update(self._threshold, self.step, self.method))

        return result
