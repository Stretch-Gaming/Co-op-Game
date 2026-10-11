import unittest
from native_csv import parse

HEADER = 'EVENTS,FrameTime,GameThreadTime,RenderThreadTime,GPUTime\n'


class NativeCsvTests(unittest.TestCase):
    def test_footer_metadata_events_and_discard(self):
        fixture = HEADER + 'start,20,10,5,8\n"event,quoted",40,30,15,18\n' + HEADER + '[HasHeaderRowAtEnd],1,[Commandline],"-game -log"\n'
        result = parse(fixture, 1)
        self.assertEqual(result['metadata']['HasHeaderRowAtEnd'], '1')
        self.assertEqual(result['metrics']['GameThreadTime']['avg_ms'], 30)
        self.assertEqual(result['metrics']['GPUTime']['samples'], 1)

    def test_missing_and_ambiguous_native_metrics(self):
        for fixture in ('EVENTS,FrameTime\n,20\n', 'EVENTS,GameThreadTime,RenderThreadTime,GPUTime,A/GPUTime\n,1,2,3,4\n'):
            with self.assertRaises(ValueError):
                parse(fixture)

    def test_invalid_negative_nonfinite(self):
        for value in ('text', '-1', 'nan', 'inf'):
            with self.assertRaises(ValueError):
                parse(HEADER + ',16,1,2,' + value + '\n')

    def test_early_columns_and_unavailable_gpu(self):
        result = parse(HEADER + ',10,1\n,16,1,2,0\n')
        self.assertEqual(result['incomplete_rows'], 1)
        self.assertTrue(any('GPU timing unavailable' in w for w in result['warnings']))
        with self.assertRaises(ValueError):
            parse(HEADER + ',16,1,2,3\n', 1)


if __name__ == '__main__':
    unittest.main()
