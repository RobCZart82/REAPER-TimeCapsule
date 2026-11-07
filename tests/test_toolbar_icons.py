import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from reaper_timecapsule.core import scan
from reaper_timecapsule.midi_validation import validate_midi_workflow
from reaper_timecapsule.toolbar_icons import audit_toolbar_icons


class ToolbarTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def audit(self, text, saved=()):
        return audit_toolbar_icons(self.root, [('reaper-menu.ini', text)], set(saved))

    def test_native_binding_fixture(self):
        fixture = Path('tests/fixtures/midi-toolbar-native.ini').read_text()
        result = self.audit(fixture)
        self.assertEqual(result['bindings_checked'], 1)
        self.assertEqual(result['issues'][0]['button'], 0)
        self.assertEqual(result['issues'][0]['icon'], 'toolbar_dock_off.png')
        self.assertEqual(result['status'], 'needs-review')

    def test_saved_file_presence_is_checked_without_loading_image(self):
        path = self.root / 'Data/toolbar_icons/synthetic.png'
        path.parent.mkdir(parents=True)
        path.write_bytes(b'synthetic presence fixture, not a valid PNG')
        result = self.audit('[Floating MIDI toolbar 1]\nicon_0=synthetic.png\nitem_0=41101 Test\n',
                            ['Data/toolbar_icons/synthetic.png'])
        self.assertEqual(result['saved_icons_available'], 1)
        self.assertEqual(result['status'], 'checked')

    def test_absolute_traversal_and_link_paths_never_followed(self):
        for icon in ('../private.png', '/private.png', 'C:\\private.png', 'sub/other.png'):
            with self.subTest(icon=icon), patch('reaper_timecapsule.toolbar_icons.trusted_resource_file') as read:
                result = self.audit('[Floating MIDI toolbar 1]\nitem_0=1 Test\nicon_0=' + icon)
                self.assertEqual(result['issue_count'], 1)
                read.assert_not_called()
        with patch('reaper_timecapsule.toolbar_icons.trusted_resource_file', side_effect=ValueError('link')):
            result = self.audit('[Floating MIDI toolbar 1]\nitem_0=1 Test\nicon_0=linked.png',
                                ['Data/toolbar_icons/linked.png'])
            self.assertEqual(result['issues'][0]['reason'], 'unreadable-or-linked-icon')

    def test_duplicate_orphan_text_and_other_sections(self):
        result = self.audit('[Floating MIDI toolbar 1]\nicon_0=a.png\nicon_1=text\nitem_1=1 A\n'
                            'icon_2=a.png\nicon_2=b.png\nitem_2=2 B\n'
                            '[Main toolbar]\nicon_0=ignored.png')
        self.assertEqual(result['issue_count'], 2)
        self.assertEqual(result['bindings_checked'], 3)

    def test_floating_midi_actions_use_midi_section(self):
        guid = 'a' * 32
        (self.root / 'reaper-menu.ini').write_text('[Floating MIDI toolbar 1]\nitem_0=_' + guid + ' Synthetic\n')
        report = validate_midi_workflow(self.root, scan(self.root))
        self.assertEqual(report['missing_custom_actions'][0]['command'], '_' + guid)
        self.assertEqual(report['status'], 'missing-dependencies')

    def test_bounded_details_with_complete_count(self):
        text = '[Floating MIDI toolbar 1]\n' + '\n'.join(f'icon_{i}=missing.png' for i in range(125))
        result = self.audit(text)
        self.assertEqual(result['issue_count'], 125)
        self.assertEqual(len(result['issues']), 100)
        self.assertTrue(result['truncated'])

    def test_oversized_numeric_index_is_reported_without_integer_conversion(self):
        result = self.audit('[Floating MIDI toolbar 1]\nicon_' + '9' * 5000 + '=private.png')
        self.assertEqual(result['issue_count'], 1)
        self.assertEqual(result['issues'][0]['reason'], 'unsupported-button-index')
