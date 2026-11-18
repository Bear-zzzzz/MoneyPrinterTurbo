import argparse
import hashlib
import json
import re
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path

from paths import ASSETS, REFERENCES


def read_url(url):
    request = urllib.request.Request(url, headers={'User-Agent': 'MoneyPrinterTurbo-GDP-example/1.0'})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def main():
    parser = argparse.ArgumentParser(description='Download the free licensed Mixkit input; not a redistributable stock bundle')
    parser.add_argument('--accept-license', action='store_true', help='Confirm that you reviewed Mixkit Free License and terms')
    args = parser.parse_args()
    record = json.loads((REFERENCES / 'stock-inputs.json').read_text())['assets'][0]
    destination = ASSETS / 'local-only' / record['filename']
    if destination.exists():
        if hashlib.sha256(destination.read_bytes()).hexdigest() != record['sha256']:
            raise SystemExit('Existing local asset has unexpected contents; refusing to replace it')
        print(f'Local asset already verified: {destination}')
        return
    if not args.accept_license:
        parser.error('Review references/free-license.html and references/terms.html, then use --accept-license')
    page = read_url(record['page']).decode('utf-8')
    if not re.search(r'href=["\']/license/#videoFree["\']', page):
        raise SystemExit('Current item page does not identify the expected free license; no download attempted')
    modal = read_url(record['download_entry']).decode('utf-8')
    match = re.search(r'data-download--modal-url-value="([^"]+)"', modal)
    if not match:
        raise SystemExit('No public download URL; sign-in/security pages are not bypassed')
    url = match.group(1)
    if urllib.parse.urlparse(url).hostname != 'assets.mixkit.co':
        raise SystemExit('Unexpected download host')
    content = read_url(url)
    if hashlib.sha256(content).hexdigest() != record['sha256']:
        raise SystemExit('Asset has changed; re-check source/license before using the new version')
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=destination.parent, delete=False) as temporary:
        temporary.write(content)
        temporary_path = Path(temporary.name)
    temporary_path.replace(destination)
    print(destination)


if __name__ == '__main__':
    main()
