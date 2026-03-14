"""
Verify that no Python files use wildcard imports (from X import *).

Wildcard imports pollute the module namespace, hide where names come
from, and can cause silent name collisions.  This test walks the
source tree and fails if any file still uses them.
"""

import ast
import os
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Directories that are not our code
SKIP_DIRS = {"venv", ".venv", "node_modules", "__pycache__", ".git"}


def _python_files():
    for dirpath, dirnames, filenames in os.walk(PROJECT_ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fname in filenames:
            if fname.endswith(".py"):
                yield os.path.join(dirpath, fname)


def _wildcard_imports(filepath):
    with open(filepath) as f:
        try:
            tree = ast.parse(f.read(), filename=filepath)
        except SyntaxError:
            return []
    results = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name == "*":
                    results.append(node.module)
    return results


class TestNoWildcardImports(unittest.TestCase):
    def test_no_wildcard_imports(self):
        violations = []
        for filepath in _python_files():
            modules = _wildcard_imports(filepath)
            for mod in modules:
                rel = os.path.relpath(filepath, PROJECT_ROOT)
                violations.append(f"{rel}: from {mod} import *")

        self.assertEqual(
            violations,
            [],
            "Wildcard imports found:\n" + "\n".join(violations),
        )


if __name__ == "__main__":
    unittest.main()
