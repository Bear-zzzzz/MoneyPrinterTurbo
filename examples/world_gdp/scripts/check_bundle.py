import hashlib
import json
from paths import PACKAGE


def main():
    manifest = json.loads((PACKAGE / 'references/bundle-manifest.json').read_text())
    for entry in manifest['files']:
        path = PACKAGE / entry['path']
        if not path.is_file():
            raise SystemExit(f'Missing file: {entry["path"]}')
        if hashlib.sha256(path.read_bytes()).hexdigest() != entry['sha256']:
            raise SystemExit(f'File differs from bundle snapshot: {entry["path"]}')
    print(f'Bundle verified: {len(manifest["files"])} files')


if __name__ == '__main__':
    main()
