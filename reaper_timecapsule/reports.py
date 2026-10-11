"""Private, versioned read-only scan reports and bounded browser pages."""
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from .core import VERSION
from .operation import checkpoint

PAGE_SIZE = 200


def scan_report(result):
    return {'report_format': 'timecapsule-scan-report', 'report_schema': 1,
            'app_version': VERSION, 'generated_utc': datetime.now(timezone.utc).isoformat(),
            'source_resource': result.get('source_resource', 'unspecified'),
            'inspection_basis': 'read-only-live-resource-scan', 'scan_completed': True,
            'transactional_snapshot': False,
            'summary': {key: result[key] for key in ('files', 'counts', 'bytes', 'portable_names_ready')},
            'entries': result['items'], 'portability_issues': result['portability_issues'],
            'inventory': result['inventory'],
            'manual_steps': ['Review unknown/machine-dependent resources before activation.',
                             'Inspect excluded links and filename portability issues.',
                             'Close REAPER before backup; verify the capsule before staged recovery.'],
            'privacy': 'Local report may contain private filenames and repository/package metadata.'}


def report_page(report, *, policy='all', query='', page=0, control=None):
    if policy not in ('all', 'keep', 'review', 'regenerate', 'exclude') or page < 0:
        raise ValueError('Invalid report filter/page')
    query = query.casefold()
    matches = []
    for entry in report['entries']:
        checkpoint(control, 'Filtering file policies')
        if (policy == 'all' or entry['policy'] == policy) and query in (entry['path'] + ' ' + entry['reason']).casefold():
            matches.append(entry)
    start = page * PAGE_SIZE
    return {'rows': matches[start:start + PAGE_SIZE], 'matches': len(matches),
            'page': page, 'page_size': PAGE_SIZE}


def export_report(report, destination, *, control=None):
    """Explicit local export; never overwrite an existing entry or follow its link."""
    path = Path(destination).expanduser().absolute()
    checkpoint(control, 'Preparing private report export')
    data = json.dumps(report, ensure_ascii=False, indent=2).encode('utf-8')
    checkpoint(control, 'Writing private report export')
    owned = None
    try:
        with path.open('xb') as output:
            metadata = os.fstat(output.fileno())
            owned = metadata.st_dev, metadata.st_ino
            for start in range(0, len(data), 1024 * 1024):
                checkpoint(control, "Writing private report export", start, len(data))
                output.write(data[start:start + 1024 * 1024])
    except BaseException:
        if owned is not None:
            try:
                metadata = path.lstat()
                if (metadata.st_dev, metadata.st_ino) == owned:
                    path.unlink()
            except OSError:
                pass
        raise
    return {'destination': str(path), 'entries': len(report['entries']), 'report_schema': 1}
