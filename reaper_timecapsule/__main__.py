"""CLI: python -m reaper_timecapsule [scan|backup|verify|restore|gui]."""
import argparse
import json
from pathlib import Path

from .core import default_resource, make_backup, preview, preview_backup, restore_backup, scan
from .midi_validation import validate_midi_workflow


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
    commands.add_parser("gui", help="Open desktop GUI")
    args = parser.parse_args()
    try:
        if args.command == "midi-audit":
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
