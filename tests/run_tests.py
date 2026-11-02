"""Run all offline regression scripts in separate processes."""
from pathlib import Path
import os
import subprocess
import sys


def main():
    failures = []
    tests = Path(__file__).resolve().parent
    root = tests.parent
    # The tests import the app modules directly, so src/ goes on the import path.
    env = dict(os.environ, PYTHONPATH=os.pathsep.join(filter(None, [str(root / 'src'), os.environ.get('PYTHONPATH')])))
    for script in sorted(tests.glob('test_*.py')):
        result = subprocess.run([sys.executable, str(script)], cwd=root, env=env)
        if result.returncode:
            failures.append(script.name)
    if failures:
        sys.exit('FAILED: ' + ', '.join(failures))
    print('All offline regression scripts passed.')


if __name__ == '__main__':
    main()
