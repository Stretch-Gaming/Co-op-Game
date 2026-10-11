import unittest
from stats import Window, summary


class TimingTests(unittest.TestCase):
    def test_known_percentiles(self):
        result = summary([40, 10, 20, 30])
        self.assertEqual(result, {'samples': 4, 'avg_ms': 25., 'p50_ms': 25., 'p95_ms': 38.5, 'max_ms': 40.})

    def test_empty_single_and_invalid(self):
        self.assertIsNone(summary([])['p95_ms'])
        self.assertEqual(summary([16])['p95_ms'], 16)
        for values in ([float('nan')], [float('inf')], [-1]):
            with self.assertRaises(ValueError):
                summary(values)

    def test_wall_window_and_timeout(self):
        window = Window(100)
        self.assertEqual([window.phase(t) for t in (100,129.99,130,159.99,160,196)],
                         ['warmup','warmup','measure','measure','finish','timeout'])

    def test_cleanup_once_on_finish_error_or_timeout(self):
        for reason in ('finish', 'error', 'timeout'):
            window, calls = Window(0), []
            window.close(lambda: calls.append(reason))
            window.close(lambda: calls.append(reason))
            self.assertEqual(calls, [reason])
            self.assertEqual(window.phase(40), 'closed')


if __name__ == '__main__':
    unittest.main()
