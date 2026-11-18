import hashlib
import json
from paths import PACKAGE, REFERENCES


def main():
    manifest_path = REFERENCES / 'bundle-manifest.json'
    files = []
    for path in sorted(PACKAGE.rglob('*')):
        if not path.is_file() or path == manifest_path:
            continue
        relative = path.relative_to(PACKAGE)
        if relative.parts[0] == 'output' or 'local-only' in relative.parts or '__pycache__' in relative.parts:
            continue
        files.append({'path': str(relative), 'size_bytes': path.stat().st_size,
                      'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    manifest_path.write_text(json.dumps({'created_on': '2026-11-18', 'files': files,
                                        'excluded': ['output/', 'assets/local-only/', '__pycache__/']}, indent=2))
    print(f'Manifest updated: {len(files)} files')


if __name__ == '__main__':
    main()
