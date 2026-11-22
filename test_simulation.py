"""Compatibility entry point for the model's numerical checks."""
import unittest
if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.discover('tests'))
    raise SystemExit(not result.wasSuccessful())
