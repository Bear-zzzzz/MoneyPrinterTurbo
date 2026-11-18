import sys
import unittest
from pathlib import Path


PACKAGE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE / 'scripts'))
sys.path.insert(0, str(PACKAGE / 'data'))
suite = unittest.defaultTestLoader.discover(str(PACKAGE / 'tests'), pattern='test_*.py')
result = unittest.TextTestRunner(verbosity=1).run(suite)
raise SystemExit(0 if result.wasSuccessful() else 1)
