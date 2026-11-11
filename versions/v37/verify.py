"""Check public file hashes and independently replay saved numerical results."""
from pathlib import Path
import hashlib
import argparse
from reproduce_tables import run

HOME = Path(__file__).resolve().parent

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', default='reproduced')
    args = parser.parse_args()
    for line in (HOME / 'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
        digest, name = line.split('  ', 1)
        path = (HOME / name).resolve()
        assert path.is_relative_to(HOME), name
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, name
    run(args.output)
