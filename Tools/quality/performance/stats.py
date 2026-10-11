"""Pure timing math. Percentiles use linear interpolation, including endpoints."""
import math


def summary(values):
    values = [float(v) for v in values]
    if any(not math.isfinite(v) or v < 0 for v in values):
        raise ValueError('Samples must be finite and nonnegative')
    if not values:
        return {'samples': 0, 'avg_ms': None, 'p50_ms': None, 'p95_ms': None, 'max_ms': None}
    ordered = sorted(values)

    def percentile(p):
        index = (len(ordered) - 1) * p
        lo = int(index)
        hi = min(lo + 1, len(ordered) - 1)
        return ordered[lo] + (ordered[hi] - ordered[lo]) * (index - lo)

    return {'samples': len(values), 'avg_ms': sum(values) / len(values),
            'p50_ms': percentile(.5), 'p95_ms': percentile(.95), 'max_ms': max(values)}


class Window:
    """Wall-time phases; a late callback triggers timeout rather than claiming success."""
    def __init__(self, start, warmup=30, measure=30, timeout=95):
        self.start, self.warmup, self.measure, self.timeout = start, warmup, measure, timeout
        self.closed = False

    def phase(self, now):
        elapsed = now - self.start
        if self.closed:
            return 'closed'
        if elapsed > self.timeout:
            return 'timeout'
        if elapsed < self.warmup:
            return 'warmup'
        if elapsed < self.warmup + self.measure:
            return 'measure'
        return 'finish'

    def close(self, unregister):
        if not self.closed:
            self.closed = True
            unregister()
