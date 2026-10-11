"""Exercise the shipped context helpers without importing Unreal or registering callbacks."""
import ast
import json
import pathlib
import sys
import types
import unittest
from unittest.mock import patch


class OptionalContextTests(unittest.TestCase):
    def test_windows_without_load_average_or_psutil_still_reports(self):
        tree = ast.parse(pathlib.Path(__file__).with_name('collect.py').read_text())
        functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
                     and node.name in ('safe', 'load_context')]
        namespace = {'os': types.SimpleNamespace(cpu_count=lambda: 8),
                     'platform': types.SimpleNamespace(platform=lambda: 'Windows test fixture')}
        exec(compile(ast.Module(body=functions, type_ignores=[]), 'context-helpers', 'exec'), namespace)
        with patch.dict(sys.modules, {'psutil': None}):
            context = namespace['load_context']()
        self.assertEqual(context['cpu_count'], 8)
        self.assertIn('unavailable', context['load_average'])
        self.assertIn('unavailable', context['cpu_percent'])
        self.assertEqual(json.loads(json.dumps(context)), context)


if __name__ == '__main__':
    unittest.main()
