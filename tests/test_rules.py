import unittest
from reaper_timecapsule.rules import decide

class RulesTests(unittest.TestCase):
    def test_portable(self):
        for name in ("Scripts/tool.lua", "MenuSets/menu.ReaperMenu", "reaper-menu.ini", "reapack.ini", "S&M.ini"):
            self.assertEqual(decide(name).policy, "keep", name)

    def test_regenerate(self):
        for name in ("reaper-vstplugins_arm64.ini", "reaper-auplugins_arm64.ini", "reaper-clap-macos-aarch64.ini", "MetadataCaches/cache"):
            self.assertEqual(decide(name).policy, "regenerate", name)

    def test_review(self):
        for name in ("reaper.ini", "UserPlugins/reaper_sws.dylib", "reaper-midihw.ini"):
            self.assertEqual(decide(name).policy, "review", name)
