"""Exact, evidence-backed preference catalogue; no inferred INI keys."""
from types import MappingProxyType

DOCUMENTATION = 'https://www.reaper.fm/sdk/walter/images.php'
APPROVED_PREFERENCES = MappingProxyType({
    ('reaper', 'tinttcp'): frozenset({'0', '1'}),
    ('reaper', 'peaksedges'): frozenset({'0', '1'}),
})


def preference_catalog():
    return {'catalog_format': 'timecapsule-preference-catalog', 'catalog_schema': 1,
            'approval_scope': 'exact section/key and restricted values only',
            'version_rule': 'caller-supplied identical REAPER 5+ versions',
            'active_writes_supported': False,
            'preferences': [{'section': section, 'key': key,
                             'accepted_values': sorted(values), 'minimum_documented_version': '5.0',
                             'status': 'approved-subset-manual-review-required',
                             'documentation_url': DOCUMENTATION,
                             'evidence': 'Official theme reference explicitly names the reaper.ini key; supported values are a restricted subset.',
                             'theme_override_possible': True}
                            for (section, key), values in sorted(APPROVED_PREFERENCES.items())],
            'not_approved': [{'key': key, 'status': 'review',
                              'reason': 'Documented as rtconfig.txt/theme directives, not evidence of an equivalent reaper.ini preference.',
                              'documentation_url': DOCUMENTATION}
                             for key in ('tcp_folderindent', 'tcp_heights', 'transport_showborders')],
            'expansion_requirements': ['Exact INI section/key evidence, not similarly named theme directives.',
                                      'Version/value-domain evidence and isolated runtime validation.',
                                      'No hardware/platform/cache/path/credential state.',
                                      'Unknown or unsupported values stay review; no active writes.']}
