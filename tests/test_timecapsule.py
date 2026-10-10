import unittest

class SmokeTest(unittest.TestCase):
    def test_import(self):
        import reaper_timecapsule
        self.assertTrue(reaper_timecapsule.VERSION)
