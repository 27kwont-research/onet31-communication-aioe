"""Record SHA-256 hashes for the distributable files after an intentional update."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_PARTS = {'.git', '.venv', '__pycache__', '.cache', 'results_reproduced'}


def main():
    files = []
    for path in sorted(ROOT.rglob('*')):
        relative = path.relative_to(ROOT)
        if not path.is_file() or any(part in EXCLUDED_PARTS for part in relative.parts):
            continue
        if path.name in {'PACKAGE_MANIFEST.json', '.DS_Store'} or path.suffix in {'.pyc', '.log'}:
            continue
        files.append({'path':relative.as_posix(),'bytes':path.stat().st_size,
                      'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    (ROOT/'PACKAGE_MANIFEST.json').write_text(json.dumps({'files':files},indent=2)+'\n')
    print(f'Recorded {len(files)} distributable files.')


if __name__ == '__main__':
    main()
