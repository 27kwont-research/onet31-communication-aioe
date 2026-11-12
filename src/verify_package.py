"""Verify package checksums and the saved numerical validation report."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    manifest = json.loads((ROOT/'PACKAGE_MANIFEST.json').read_text())
    for item in manifest['files']:
        path = ROOT/item['path']
        if not path.is_file():
            raise ValueError(f'Missing package file: {item["path"]}')
        if hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256']:
            raise ValueError(f'Checksum mismatch: {item["path"]}')
    report = json.loads((ROOT/'results/verification.json').read_text())
    for key in ['raw_checksums_verified','archived_k4_partition_reproduced','candidate_k_metrics_reproduced']:
        if report[key] is not True:
            raise ValueError(f'Failed numerical validation: {key}')
    print(f'Verified {len(manifest["files"])} files and the saved numerical validation report.')


if __name__ == '__main__':
    main()
