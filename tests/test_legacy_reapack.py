"""Legacy ReaPack archives are migrated using CURRENT safety policies."""
import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from reaper_timecapsule.core import make_backup, restore_backup, verify_backup, preview_backup


class LegacyReaPackArchiveTests(unittest.TestCase):
    def test_old_registry_quarantined_and_old_cache_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source = base / "source"
            (source / "ReaPack").mkdir(parents=True)
            (source / "ReaPack/registry.db").write_bytes(b"legacy sample registry")
            archive = base / "snapshot.zip"
            make_backup(source, archive)
            with zipfile.ZipFile(archive) as zip_in:
                entries = {name: zip_in.read(name) for name in zip_in.namelist()}
            manifest = json.loads(entries["manifest.json"].decode("utf-8"))
            manifest["app_version"] = "0.4.0-dev"
            manifest.pop("inventory_basis", None)
            for item in manifest["files"]:
                if item["path"] == "ReaPack/registry.db":
                    item["policy"] = "keep"
            old_cache_bytes = b"previously downloaded cache"
            cache_name = "ReaPack/cache/old.xml"
            manifest["files"].append({
                "path": cache_name,
                "size": len(old_cache_bytes),
                "sha256": hashlib.sha256(old_cache_bytes).hexdigest(),
                "policy": "keep",
                "reason": "portable user resource",
            })
            entries["resources/" + cache_name] = old_cache_bytes
            entries["manifest.json"] = json.dumps(manifest).encode("utf-8")
            with zipfile.ZipFile(archive, "w") as z:
                for name, data in entries.items():
                    z.writestr(name, data)
            self.assertEqual(verify_backup(archive)["schema"], 2)
            before = preview_backup(archive)
            self.assertEqual(before['stored_saved'], {'keep': 2})
            self.assertEqual(before['saved'], {'review': 1, 'regenerate': 1})
            self.assertEqual(len(before['policy_changes']), 2)
            self.assertTrue(all(x['reason'] for x in before['policy_changes']))
            self.assertEqual(before['inventory_basis'], 'legacy-unverified-source-inventory')
            out = base / "Recovered"
            report = restore_backup(archive, out)
            self.assertEqual(report["isolated_for_review"], 1)
            self.assertEqual(report["legacy_cache_skipped"], 1)
            self.assertTrue((out / "NeedsReview/ReaPack/registry.db").exists())
            self.assertFalse((out / "REAPER/ReaPack/registry.db").exists())
            self.assertFalse((out / "REAPER/ReaPack/cache/old.xml").exists())
            self.assertFalse((out / "NeedsReview/ReaPack/cache/old.xml").exists())

    def test_current_version_rejects_forged_registry_policy(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source = base / "source"
            (source / "ReaPack").mkdir(parents=True)
            (source / "ReaPack/registry.db").write_bytes(b"sample")
            archive = base / "snapshot.zip"
            make_backup(source, archive)
            with zipfile.ZipFile(archive) as z:
                entries = {n: z.read(n) for n in z.namelist()}
            manifest = json.loads(entries["manifest.json"])
            manifest["files"][0]["policy"] = "keep"
            entries["manifest.json"] = json.dumps(manifest).encode("utf-8")
            with zipfile.ZipFile(archive, "w") as z:
                for name, data in entries.items():
                    z.writestr(name, data)
            with self.assertRaises(ValueError):
                verify_backup(archive)


if __name__ == "__main__":
    unittest.main()
