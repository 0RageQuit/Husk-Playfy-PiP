"""Generate a removable Home Screen Web Clip from the user's own launch profiles."""
import argparse
import base64
import plistlib
import re
import uuid
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


def webclip(profile):
    clips = [p for p in profile.get('PayloadContent', [])
             if p.get('PayloadType') == 'com.apple.webClip.managed']
    if len(clips) != 1:
        raise ValueError('Choose a profile containing exactly one Web Clip.')
    return clips[0]


def generate(husk_url, livecontainer_url, name='PLAYFy', icon=None):
    inner = urlsplit(husk_url.strip())
    inner_query = dict(parse_qsl(inner.query))
    identifier = inner_query.get('unique_identifier', '')
    if inner.scheme.lower() != 'husk' or inner.netloc.lower() != 'open_app' or not identifier:
        raise ValueError('The Husk link must be husk://open_app?unique_identifier=YOUR-IMPORT-ID.')
    outer = urlsplit(livecontainer_url.strip())
    query = parse_qsl(outer.query, keep_blank_values=True)
    if (not outer.scheme or outer.scheme.lower() in ['http', 'https', 'file']
            or outer.netloc.lower() != 'livecontainer-launch'
            or not dict(query).get('bundle-name')):
        raise ValueError('Choose the launch link/profile for the Husk guest inside LiveContainer.')
    query = [(k, v) for k, v in query if k != 'open-url']
    query.append(('open-url', base64.b64encode(husk_url.strip().encode()).decode()))
    launch = urlunsplit((outer.scheme, outer.netloc, outer.path, urlencode(query), ''))
    safe = re.sub(r'[^a-z0-9.-]', '-', identifier.lower())
    payload_id = 'local.husk.videopip.' + safe
    clip = {
        'PayloadType': 'com.apple.webClip.managed', 'PayloadVersion': 1,
        'PayloadIdentifier': payload_id + '.webclip', 'PayloadUUID': str(uuid.uuid4()),
        'PayloadDisplayName': name, 'Label': name, 'URL': launch,
        'FullScreen': True, 'IgnoreManifestScope': True,
        'IsRemovable': True, 'Precomposed': True,
    }
    if icon:
        clip['Icon'] = icon
    return {
        'PayloadType': 'Configuration', 'PayloadVersion': 1,
        'PayloadIdentifier': payload_id, 'PayloadUUID': str(uuid.uuid4()),
        'PayloadDisplayName': name + ' (Husk in LiveContainer)',
        'PayloadDescription': 'Adds a Home Screen launcher for the existing Husk import in LiveContainer.',
        'PayloadRemovalDisallowed': False, 'PayloadContent': [clip],
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--husk-profile', type=Path, required=True)
    p.add_argument('--livecontainer-profile', type=Path, required=True)
    p.add_argument('--name')
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    if a.output.exists():
        p.error('Output already exists; choose a new name to preserve it.')
    try:
        h = webclip(plistlib.loads(a.husk_profile.read_bytes()))
        lc = webclip(plistlib.loads(a.livecontainer_profile.read_bytes()))
        result = generate(h['URL'], lc['URL'], a.name or h.get('Label', 'PLAYFy'), h.get('Icon'))
        a.output.write_bytes(plistlib.dumps(result, fmt=plistlib.FMT_XML))
    except (ValueError, KeyError, plistlib.InvalidFileException) as e:
        p.error(str(e))
    print('Created', a.output, '- not installed.')


if __name__ == '__main__':
    main()
