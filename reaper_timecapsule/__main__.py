"""CLI: python -m reaper_timecapsule [scan|backup|verify|restore|gui]."""
import argparse
import json
from pathlib import Path

from .core import default_resource, make_backup, preview, preview_backup, restore_backup, scan
from .midi_validation import validate_midi_workflow
from .reapack_profile import inspect_registry, parse_profile
from .config_migration import preview_migration
from .theme_migration import preview_themes
from .config_staging import export_preferences, verify_staging


def main():
    parser = argparse.ArgumentParser(description="REAPER TimeCapsule - safe backup and restore")
    commands = parser.add_subparsers(dest="command", required=True)
    scan_cmd = commands.add_parser("scan", help="Preview backup policies")
    scan_cmd.add_argument("source", nargs="?", type=Path, default=default_resource())
    backup_cmd = commands.add_parser("backup", help="Create ZIP snapshot without overwriting")
    backup_cmd.add_argument("archive", type=Path)
    backup_cmd.add_argument("--source", type=Path, default=default_resource())
    verify_cmd = commands.add_parser("verify", help="Verify ZIP checksums and policy")
    verify_cmd.add_argument("archive", type=Path)
    restore_cmd = commands.add_parser("restore", help="Restore to a NEW folder, no active overwrite")
    restore_cmd.add_argument("archive", type=Path)
    restore_cmd.add_argument("destination", type=Path)
    midi_cmd = commands.add_parser("midi-audit", help="Validate MIDI menus, Custom Actions and script registrations")
    midi_cmd.add_argument("source", nargs="?", type=Path, default=default_resource())
    rp_cmd = commands.add_parser("reapack-audit", help="Inspect ReaPack repository options and installed package registry")
    rp_cmd.add_argument("source", nargs="?", type=Path, default=default_resource())
    migration_cmd = commands.add_parser("config-preview", help="Read-only reaper.ini migration diff")
    migration_cmd.add_argument("source", type=Path)
    migration_cmd.add_argument("target", type=Path)
    migration_cmd.add_argument("--source-version")
    migration_cmd.add_argument("--target-version")
    theme_cmd = commands.add_parser("theme-preview", help="Read-only factory/user theme comparison")
    theme_cmd.add_argument("source", type=Path)
    theme_cmd.add_argument("factory", type=Path)
    theme_cmd.add_argument("target", type=Path)
    theme_cmd.add_argument("--source-version")
    theme_cmd.add_argument("--factory-version")
    staging_cmd = commands.add_parser("config-stage", help="Opt-in export of selected preference DATA only")
    staging_cmd.add_argument("source", type=Path)
    staging_cmd.add_argument("target", type=Path)
    staging_cmd.add_argument("archive", type=Path)
    staging_cmd.add_argument("--select", action="append", required=True)
    staging_cmd.add_argument("--source-version", required=True)
    staging_cmd.add_argument("--target-version", required=True)
    staging_cmd.add_argument("--opt-in", action="store_true")
    staging_verify = commands.add_parser("verify-stage", help="Read-only staging integrity and policy check")
    staging_verify.add_argument("archive", type=Path)
    staging_verify.add_argument("--target", type=Path)
    commands.add_parser("gui", help="Open desktop GUI")
    args = parser.parse_args()
    try:
        if args.command == "config-stage":
            result = export_preferences(args.source, args.target, args.archive,
                                        selections=args.select, source_version=args.source_version,
                                        target_version=args.target_version, opt_in=args.opt_in)
        elif args.command == "verify-stage":
            result = verify_staging(args.archive, target=args.target)
        elif args.command == "theme-preview":
            result = preview_themes(args.source, args.factory, args.target,
                                    source_version=args.source_version,
                                    factory_version=args.factory_version)
        elif args.command == "config-preview":
            result = preview_migration(args.source, args.target,
                                       source_version=args.source_version,
                                       target_version=args.target_version)
        elif args.command == "reapack-audit":
            result = {
                "profile": parse_profile(args.source / "reapack.ini"),
                "registry": inspect_registry(args.source / "ReaPack" / "registry.db"),
            }
        elif args.command == "midi-audit":
            result = validate_midi_workflow(args.source, scan(args.source))
        elif args.command == "scan":
            result = preview(args.source)
        elif args.command == "backup":
            result = make_backup(args.source, args.archive)
        elif args.command == "verify":
            result = preview_backup(args.archive)
        elif args.command == "restore":
            result = restore_backup(args.archive, args.destination)
        else:
            from .gui import App
            App().mainloop()
            return
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (ValueError, OSError, KeyError) as exc:
        parser.exit(1, f"TimeCapsule error: {exc}\n")


if __name__ == "__main__":
    main()
