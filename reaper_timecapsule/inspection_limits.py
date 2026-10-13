"""Public inspection budgets, without inspecting user files or changing limits."""
from . import core, midi_validation, reapack_profile, config_migration, config_staging
from .resource_budget import MAX_CENTRAL_DIRECTORY, SPACE_MARGIN


def inspection_limits():
    return {
        "report_format": "timecapsule-inspection-limits", "report_schema": 1,
        "app_version": core.VERSION, "user_configurable": False,
        "archive": {"source_records": core.MAX_FILES, "zip_members": core.MAX_FILES + 1,
                    "manifest_bytes": core.MAX_MANIFEST_BYTES,
                    "central_directory_bytes": MAX_CENTRAL_DIRECTORY,
                    "single_file_bytes": core.MAX_SINGLE_FILE,
                    "total_payload_bytes": core.MAX_TOTAL_BYTES,
                    "free_space_margin_bytes": SPACE_MARGIN},
        "midi": {"text_file_bytes": midi_validation.MAX_TEXT_BYTES,
                 "issue_details_per_category": midi_validation.MAX_ISSUES},
        "reapack": {"ini_bytes": reapack_profile.MAX_INI_BYTES,
                    "registry_bytes": reapack_profile.MAX_REGISTRY_BYTES,
                    "repositories": reapack_profile.MAX_REMOTES,
                    "package_details": reapack_profile.MAX_PACKAGES},
        "configuration": {"ini_bytes": config_migration.MAX_BYTES,
                          "staging_archive_bytes": config_staging.MAX_ARCHIVE_BYTES},
        "notes": ["Inspection budgets are not operating-system memory/CPU or I/O guarantees.",
                  "Free-space estimates are not reservations.",
                  "MIDI issue and ReaPack package detail limits shorten reports; inspect truncation/status fields.",
                  "Source-record limits do not bound traversal of empty directories.",
                  "This command reads no resource files and changes no settings."],
    }


def inspection_limits_text():
    report = inspection_limits()
    lines = ["Fixed limits for this build (not user-configurable):"]
    for section in ("archive", "midi", "reapack", "configuration"):
        lines.append("\n" + section.capitalize())
        for key, value in report[section].items():
            if key.endswith("_bytes"):
                unit, divisor = ("GiB", 1024 ** 3) if value >= 1024 ** 3 else ("MiB", 1024 ** 2)
                text = f"{value / divisor:g} {unit}"
            else:
                text = f"{value:,}"
            lines.append(f"  {key.replace('_', ' ')}: {text}")
    return "\n".join(lines + ["", *report["notes"]])
