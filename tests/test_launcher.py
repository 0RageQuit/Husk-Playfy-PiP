import base64
import plistlib
import sys
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'shortcuts'))
from make_launcher import generate, webclip


class LauncherTests(unittest.TestCase):
    def test_route_fullscreen_and_icon(self):
        inner = 'husk://open_app?unique_identifier=test-import'
        outer = 'livecontainer2://livecontainer-launch?bundle-name=husk.app&container-folder-name=test-container&jit=true'
        p = plistlib.loads(plistlib.dumps(generate(inner, outer, 'PLAYFy & TV', b'test-icon')))
        c = webclip(p)
        q = parse_qs(urlsplit(c['URL']).query)
        self.assertTrue(c['FullScreen'])
        self.assertTrue(c['IsRemovable'])
        self.assertEqual(c['Icon'], b'test-icon')
        self.assertEqual(c['Label'], 'PLAYFy & TV')
        self.assertEqual(urlsplit(c['URL']).scheme, 'livecontainer2')
        self.assertEqual(q['container-folder-name'], ['test-container'])
        self.assertEqual(q['jit'], ['true'])
        self.assertEqual(base64.b64decode(q['open-url'][0]).decode(), inner)

    def test_replace_old_nested_url(self):
        p = generate('husk://open_app?unique_identifier=another-import',
                     'livecontainer://livecontainer-launch?bundle-name=husk.app&open-url=old')
        q = parse_qs(urlsplit(webclip(p)['URL']).query)
        self.assertEqual(len(q['open-url']), 1)
        self.assertEqual(len(p['PayloadContent']), 1)

    def test_reject_wrong_inputs(self):
        for inner, outer in [
            ('https://example.invalid', 'livecontainer://livecontainer-launch?bundle-name=husk.app'),
            ('husk://open_app', 'livecontainer://livecontainer-launch?bundle-name=husk.app'),
            ('husk://open_app?unique_identifier=x', 'https://example.invalid'),
            ('husk://open_app?unique_identifier=x', 'livecontainer://livecontainer-launch'),
        ]:
            with self.assertRaises(ValueError):
                generate(inner, outer)


if __name__ == '__main__':
    unittest.main()
