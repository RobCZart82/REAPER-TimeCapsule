"""ReaPack 1.x configuration/registry fixtures only, never real user data."""
from __future__ import annotations

import sqlite3
from io import BytesIO
from unittest.mock import Mock, patch
import tempfile
import unittest
from pathlib import Path

from reaper_timecapsule.core import make_backup, preview, preview_backup, restore_backup
from reaper_timecapsule.reapack_profile import inspect_registry, parse_profile
from reaper_timecapsule.rules import decide


class ReaPackProfileTests(unittest.TestCase):
    def setUp(self):
        context = tempfile.TemporaryDirectory()
        self.addCleanup(context.cleanup)
        self.root = Path(context.name) / "REAPER"
        self.root.mkdir()

    def put(self, relative: str, value: str):
        file = self.root / relative
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(value, encoding="utf-8")
        return file

    def standard_ini(self):
        """Synthetic version-4 ReaPack 1.x schema, based on upstream config.cpp."""
        return self.put("reapack.ini", "\n".join([
            "[general]", "version=4",
            "[install]", "autoinstall=1", "prereleases=0", "promptobsolete=1",
            "[browser]", "synonyms=1",
            "[remotes]", "size=4",
            "remote0=ReaPack|https://reapack.com/index.xml|1|2",
            "remote1=FTC Tools|https://raw.githubusercontent.com/iliaspoulakis/Reaper-Tools/master/index.xml|1|2",
            "remote2=TK Scripts|https://raw.githubusercontent.com/TouristKiller/TK-Scripts/master/index.xml|1|0",
            "remote3=ReaTeam Themes|https://github.com/ReaTeam/Themes/raw/master/index.xml|0|2",
            "",
        ]))

    def test_parser_exact_repository_states(self):
        report = parse_profile(self.standard_ini())
        self.assertEqual(report["status"], "parsed")
        self.assertEqual(report["repository_count"], 4)
        self.assertEqual(report["enabled_count"], 3)
        self.assertEqual(report["disabled_count"], 1)
        self.assertEqual(report["repositories"][3]["name"], "ReaTeam Themes")
        self.assertFalse(report["repositories"][3]["enabled"])
        self.assertFalse(report["repositories"][2]["auto_install_override"])
        self.assertIsNone(report["repositories"][0]["auto_install_override"])

    def test_global_options_explicit(self):
        options = parse_profile(self.standard_ini())["options"]
        self.assertTrue(options["install_new_on_sync"]["value"])
        self.assertFalse(options["enable_prereleases"]["value"])
        self.assertTrue(options["prompt_to_uninstall_obsolete"]["value"])
        self.assertTrue(options["expand_search_synonyms"]["value"])
        self.assertEqual(options["install_new_on_sync"]["origin"], "explicit")

    def test_ten_repository_profile_preserves_disabled_entries(self):
        # Synthetic data matching the 10-row shape of the user-provided
        # ReaPack repository manager screenshot, not a copied private INI.
        rows = [
            ("ReaPack", "https://reapack.com/index.xml", 1),
            ("ReaTeam Scripts", "https://github.com/ReaTeam/ReaScripts/raw/master/index.xml", 1),
            ("ReaTeam JSFX", "https://github.com/ReaTeam/JSFX/raw/master/index.xml", 1),
            ("ReaTeam Themes", "https://github.com/ReaTeam/Themes/raw/master/index.xml", 0),
            ("ReaTeam LangPacks", "https://github.com/ReaTeam/LangPacks/raw/master/index.xml", 0),
            ("ReaTeam Extensions", "https://github.com/ReaTeam/Extensions/raw/master/index.xml", 1),
            ("MPL Scripts", "https://github.com/MichaelPilyavskiy/ReaScripts/raw/master/index.xml", 1),
            ("X-Raym Scripts", "https://github.com/X-Raym/REAPER-ReaScripts/raw/master/index.xml", 1),
            ("FTC Tools", "https://raw.githubusercontent.com/iliaspoulakis/Reaper-Tools/master/index.xml", 1),
            ("TK Scripts", "https://raw.githubusercontent.com/TouristKiller/TK-Scripts/master/index.xml", 1),
        ]
        ini_text = "\n".join([
            "[general]", "version=4", "[remotes]", "size=10",
            *(f"remote{i}={name}|{url}|{enabled}|2"
              for i, (name, url, enabled) in enumerate(rows)),
            "",
        ])
        report = parse_profile(self.put("reapack.ini", ini_text))
        self.assertEqual(report["status"], "parsed")
        self.assertEqual(report["repository_count"], 10)
        self.assertEqual(report["enabled_count"], 8)
        self.assertEqual(report["disabled_count"], 2)
        self.assertEqual([x["name"] for x in report["repositories"] if not x["enabled"]],
                         ["ReaTeam Themes", "ReaTeam LangPacks"])

    def test_source_defaults_preserved_when_missing(self):
        ini = self.put("reapack.ini", "[general]\nversion=4\n[remotes]\nsize=0\n")
        parsed = parse_profile(ini)
        self.assertEqual(parsed["status"], "parsed")
        self.assertFalse(parsed["options"]["install_new_on_sync"]["value"])
        self.assertTrue(parsed["options"]["prompt_to_uninstall_obsolete"]["value"])
        self.assertEqual(parsed["options"]["expand_search_synonyms"]["origin"], "upstream-default")

    def test_no_guess_when_broken_state(self):
        ini = self.put("reapack.ini", "[general]\nversion=4\n[remotes]\nsize=2\nremote0=Broken\n")
        parsed = parse_profile(ini)
        self.assertEqual(parsed["status"], "partial")
        self.assertEqual(parsed["enabled_count"], 0)
        self.assertTrue(parsed["notes"])

    def test_future_version_not_guessed(self):
        ini = self.put("reapack.ini", "[general]\nversion=200\n[remotes]\nsize=0\n")
        self.assertEqual(parse_profile(ini)["status"], "unsupported")

    def test_url_password_and_query_redacted(self):
        ini = self.put("reapack.ini", (
            "[remotes]\nsize=1\n"
            "remote0=Private|https://user:pass@example.org/Some/index.xml?token=example#frag|1|2\n"
        ))
        obj = parse_profile(ini)
        self.assertEqual(obj["repositories"][0]["index_url"], "https://example.org/Some/index.xml")
        self.assertNotIn("pass", str(obj))
        self.assertNotIn("token", str(obj))
        self.assertFalse(obj["automatic_sync"])

    def test_duplicate_ini_keys_fail_closed(self):
        ini = self.put("reapack.ini", (
            "[remotes]\nsize=1\nremote0=A|https://a.org/index.xml|1|2\n"
            "remote0=B|https://b.org/index.xml|0|2\n"
        ))
        self.assertEqual(parse_profile(ini)["status"], "invalid")

    def test_invalid_override_is_not_reported_as_valid_inheritance(self):
        for override in ("", "3", "yes", "private-invalid-value"):
            with self.subTest(override=override):
                ini = self.put("reapack.ini", "[remotes]\nsize=2\n"
                               "remote0=Bad|https://user:secret@example.org/index.xml?token=private|1|" + override + "\n"
                               "remote1=Good|https://good.example/index.xml|0|2\n")
                original = ini.read_bytes()
                parsed = parse_profile(ini)
                self.assertEqual(parsed["status"], "partial")
                self.assertEqual([row["name"] for row in parsed["repositories"]], ["Good"])
                self.assertIn("1 malformed", parsed["notes"][0])
                self.assertNotIn("private", str(parsed))
                self.assertNotIn("secret", str(parsed))
                self.assertEqual(ini.read_bytes(), original)

    def test_valid_override_and_legacy_omission_remain_supported(self):
        for suffix, expected in (("", None), ("|0", False), ("|1", True), ("|2", None)):
            with self.subTest(suffix=suffix):
                ini = self.put("reapack.ini", "[remotes]\nsize=1\nremote0=Good|https://example.org/index.xml|1" + suffix + "\n")
                parsed = parse_profile(ini)
                self.assertEqual(parsed["status"], "parsed")
                self.assertIs(parsed["repositories"][0]["auto_install_override"], expected)

    def test_ini_read_is_bounded_if_file_grows_after_stat(self):
        from reaper_timecapsule.inventory import _public_repo_urls
        ini = self.put("reapack.ini", "small")
        for reader in (parse_profile, _public_repo_urls):
            with self.subTest(reader=reader.__name__):
                stream = BytesIO(b"x" * 100)
                stream.read = Mock(wraps=stream.read)
                with patch("reaper_timecapsule.reapack_profile.MAX_INI_BYTES", 64), \
                     patch("reaper_timecapsule.inventory.MAX_REAPACK_INI_BYTES", 64), \
                     patch.object(Path, "open", return_value=stream):
                    result = reader(ini)
                stream.read.assert_called_once_with(65)
                if reader is parse_profile:
                    self.assertEqual(result["status"], "too-large")
                else:
                    self.assertEqual(result, [])

    def test_backup_inventory_retains_repository_profile(self):
        self.standard_ini()
        archive = self.root.parent / "snapshot.zip"
        make_backup(self.root, archive)
        report = preview_backup(archive)["inventory"]["reapack"]
        self.assertEqual(report["profile"]["enabled_count"], 3)
        self.assertEqual(report["profile"]["disabled_count"], 1)
        self.assertEqual(report["repository_states"], "parsed-from-reapack-ini")

    def test_db_is_review_only_and_cache_regenerated(self):
        self.assertEqual(decide("ReaPack/registry.db").policy, "review")
        self.assertEqual(decide("ReaPack/registry.db-wal").policy, "review")
        self.assertEqual(decide("ReaPack/registry.db-shm").policy, "regenerate")
        self.assertEqual(decide("ReaPack/cache/FTC Tools.xml").policy, "regenerate")
        self.assertEqual(decide("ReaPack/cache/subfolder/index.xml").policy, "regenerate")


class ReaPackRegistryTests(unittest.TestCase):
    def setUp(self):
        context = tempfile.TemporaryDirectory()
        self.addCleanup(context.cleanup)
        self.source = Path(context.name) / "REAPER"
        self.source.mkdir()
        self.registry = self.source / "ReaPack" / "registry.db"
        self.registry.parent.mkdir()

    def database(self):
        db = sqlite3.connect(self.registry)
        db.executescript(
            "CREATE TABLE entries (id INTEGER PRIMARY KEY, remote TEXT, category TEXT,"
            " package TEXT, version TEXT, flags INTEGER);"
            "CREATE TABLE files (id INTEGER PRIMARY KEY, entry INTEGER, path TEXT);"
        )
        db.execute(
            "INSERT INTO entries VALUES (1,?,?,?,?,?)",
            ("FTC Tools", "Scripts", "Chordbox.lua", "1.2", 1),
        )
        db.execute(
            "INSERT INTO entries VALUES (2,?,?,?,?,?)",
            ("TK Scripts", "Scripts", "Gridbox.lua", "2.0", 2),
        )
        db.execute("INSERT INTO files VALUES (1, 1, 'Scripts/Chordbox.lua')")
        db.execute("INSERT INTO files VALUES (2, 1, 'Scripts/Chordbox-icon.png')")
        db.execute("INSERT INTO files VALUES (3, 2, 'Scripts/Gridbox.lua')")
        db.commit()
        db.close()

    def test_sqlite_registry_packages_and_flags(self):
        self.database()
        report = inspect_registry(self.registry)
        self.assertEqual(report["status"], "parsed")
        self.assertEqual(report["installed_count"], 2)
        self.assertEqual(report["owned_file_count"], 3)
        self.assertEqual(report["installed_packages"][0]["owned_files"], 2)
        self.assertTrue(report["installed_packages"][0]["pinned"])
        self.assertTrue(report["installed_packages"][1]["prerelease_override"])

    def test_database_in_restore_is_isolated(self):
        self.database()
        archive = self.source.parent / "snapshot.zip"
        make_backup(self.source, archive)
        report = preview_backup(archive)["inventory"]["reapack"]
        self.assertEqual(report["registry"]["installed_count"], 2)
        output = self.source.parent / "Recovered"
        restore_backup(archive, output)
        self.assertTrue((output / "NeedsReview/ReaPack/registry.db").exists())
        self.assertFalse((output / "REAPER/ReaPack/registry.db").exists())

    def test_unknown_sqlite_schema(self):
        self.registry.write_bytes(b"not a sqlite database")
        self.assertEqual(inspect_registry(self.registry)["status"], "unsupported")

    def test_wal_sidecar_guard(self):
        self.database()
        (self.source / "ReaPack" / "registry.db-wal").write_bytes(b"pending-wal")
        self.assertEqual(inspect_registry(self.registry)["status"], "busy-or-incomplete")


if __name__ == "__main__":
    unittest.main()
