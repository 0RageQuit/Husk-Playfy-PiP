"""Read-only USB metadata helper; creates a profile locally, never installs it."""
import argparse
import asyncio
import plistlib
from pathlib import Path
from urllib.parse import urlencode

from make_launcher import generate


async def run(a):
    from pymobiledevice3.lockdown import create_using_usbmux
    from pymobiledevice3.services.house_arrest import HouseArrestService
    from pymobiledevice3.services.installation_proxy import InstallationProxyService
    async with await create_using_usbmux(connection_type='USB') as dev:
        async with InstallationProxyService(dev) as service:
            apps = await service.get_apps(application_type='User')
        choices = [key for key in apps if 'livecontainer' in key.lower()]
        if a.livecontainer_bundle:
            choices = [a.livecontainer_bundle] if a.livecontainer_bundle in apps else []
        if len(choices) != 1:
            raise ValueError('Choose --livecontainer-bundle from: ' + ', '.join(choices))
        bundle = choices[0]
        schemes = [s for t in apps[bundle].get('CFBundleURLTypes', [])
                   for s in t.get('CFBundleURLSchemes', []) if s.startswith('livecontainer')]
        if not schemes:
            raise ValueError('No LiveContainer launch scheme was found.')
        async with await HouseArrestService.create(dev, bundle, documents_only=True) as afc:
            guests = []
            for folder in await afc.listdir('/Documents/Applications'):
                if not folder.endswith('.app'):
                    continue
                try:
                    info = plistlib.loads(await afc.get_file_contents('/Documents/Applications/' + folder + '/Info.plist'))
                    if ('husk' in folder.lower() or info.get('CFBundleIdentifier') == 'com.husk.app'):
                        guests.append(folder)
                except Exception:
                    continue
            if len(guests) != 1:
                raise ValueError('Expected one Husk guest, found: ' + ', '.join(guests))
            guest = guests[0]
            cfg = plistlib.loads(await afc.get_file_contents('/Documents/Applications/' + guest + '/LCAppInfo.plist'))
            container = cfg['LCDataUUID']
            if '/' in container or '\\' in container or not container:
                raise ValueError('Invalid data-container identifier.')
            root = '/Documents/Data/Application/' + container + '/Documents/TranslationLayer'
            imports = []
            for identifier in await afc.listdir(root):
                if '/' in identifier or '\\' in identifier or identifier in ['.', '..']:
                    continue
                try:
                    label = (await afc.get_file_contents(root + '/' + identifier + '/label.txt')).decode().strip()
                    if ('playfy' in label.lower() and not a.import_id) or identifier == a.import_id:
                        imports.append((identifier, label))
                except Exception:
                    continue
            if len(imports) != 1:
                raise ValueError('Choose --import-id; matching imports: ' + ', '.join(i for i, _ in imports))
            identifier, label = imports[0]
            try:
                icon = await afc.get_file_contents(root + '/' + identifier + '/icon.png')
            except Exception:
                icon = None
            inner = 'husk://open_app?' + urlencode({'unique_identifier': identifier})
            outer = schemes[0] + '://livecontainer-launch?' + urlencode({'bundle-name': guest, 'container-folder-name': container})
            profile = generate(inner, outer, label, icon)
            a.output.write_bytes(plistlib.dumps(profile, fmt=plistlib.FMT_XML))
            print('Created', a.output, 'for', label, '- nothing installed or written to the phone.')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--livecontainer-bundle')
    p.add_argument('--import-id')
    a = p.parse_args()
    if a.output.exists():
        p.error('Output exists; choose another name to preserve it.')
    try:
        asyncio.run(run(a))
    except (ValueError, KeyError) as e:
        p.error(str(e))
