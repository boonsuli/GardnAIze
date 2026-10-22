"""Check that source files use four-space indentation without tab characters."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUFFIXES = {".ts", ".html", ".scss", ".css", ".py", ".java", ".sql"}
TARGETS = [ROOT / "frontend", ROOT / "ai-service"]
IGNORED = {"node_modules", "dist", ".angular", "__pycache__", ".venv", "venv"}
failures = []

for target in TARGETS:
    for path in target.rglob("*"):
        if not path.is_file() or path.suffix not in SUFFIXES:
            continue
        if any(part in IGNORED for part in path.relative_to(target).parts):
            continue
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            prefix = line[: len(line) - len(line.lstrip(" \t"))]
            if "\t" in prefix or (len(prefix) % 4 and line.strip()):
                failures.append(f"{path.relative_to(ROOT)}:{number}: indentation is not 4 spaces")

if failures:
    raise SystemExit("\n".join(failures))

print("Indentation check passed.")
