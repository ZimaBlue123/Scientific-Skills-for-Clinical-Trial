"""Stage and commit the docx_utils fix."""

import subprocess
from pathlib import Path

cwd = Path(r"E:\Cursor Project\2-Scientific-Skills-for-Clinical_Trial")


def run(*args):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)


# 1. Stage
res = run("add", "scripts/common_scripts/docx_utils.py")
print("git add:", res.returncode, res.stderr)

# 2. Confirm staged
res = run("status", "--short")
print("status after add:")
print(res.stdout)

# 3. Commit with proper message
msg = """fix(scripts): add pathlib import to fix F821 undefined name 'Path'

CI was failing on commit 8768d0d with:
  scripts/common_scripts/docx_utils.py:161:16: F821 undefined name 'Path'

Root cause: the new convert_doc_to_docx() helper returned
'Path(str(output_path))' but the module-level pathlib import was
missing.

Additionally fixes:
 * F811 redefinition of unused '_os' in convert_doc_to_docx()
   (the same import was duplicated inside the function body)

Self-check: full scripts/ tree (36 .py files, excl. _archive and
_selftest_*) passes pyflakes 3.4 with 0 errors.
"""
res = run("commit", "-m", msg)
print()
print("git commit:", res.returncode)
print(res.stdout)
print(res.stderr)

# 4. Show last commits
res = run("log", "--oneline", "-3")
print(res.stdout)
