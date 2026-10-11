import sys
import zipfile
from pathlib import PurePosixPath
from pathlib import Path

source = Path(sys.argv[1] if len(sys.argv) > 1 else "aws-monitor-source.zip")
output = Path("aws-monitor-review-bundle.md")

skip_dirs = {
    ".git", ".venv", "venv", "__pycache__",
    "node_modules", "bin", "obj", ".vs",
    ".pytest_cache", ".mypy_cache"
}

extensions = {
    ".py", ".cs", ".xaml", ".csproj", ".sln",
    ".props", ".targets", ".json", ".md", ".txt",
    ".toml", ".yaml", ".yml", ".xml", ".config",
    ".ini", ".ps1", ".bat", ".sh"
}

skip_names = {
    ".env", "package-lock.json", "yarn.lock",
    "poetry.lock", "uv.lock"
}

priority = [
    "run_pipeline.py",
    "requirements.txt",
    "pyproject.toml",
    "src/preprocessing/",
    "src/features/",
    "src/ml/",
    "src/detection/",
    "src/validation/",
    "src/explainability/",
    "src/api/",
    "tests/",
    "ui/",
    "models/",
    "docs/",
    "README.md",
]

def rank(path):
    for i, prefix in enumerate(priority):
        if path == prefix or path.startswith(prefix):
            return i
    return len(priority)

if not source.is_file():
    raise SystemExit(f"ZIP not found: {source.resolve()}")

with zipfile.ZipFile(source) as archive:
    members = []

    for info in archive.infolist():
        if info.is_dir():
            continue

        path = PurePosixPath(info.filename)

        if any(part in skip_dirs for part in path.parts):
            continue

        if path.name in skip_names or path.name.startswith(".env"):
            continue

        members.append(info)

    with output.open("w", encoding="utf-8") as out:
        out.write("# AWS-Monitor Source Review Bundle\n\n")
        out.write(f"Archive: {source.name}\n")
        out.write(f"Files inventoried: {len(members)}\n\n")
        out.write("## Repository Inventory\n\n")

        for info in sorted(members, key=lambda x: x.filename.lower()):
            out.write(
                f"- `{info.filename}` "
                f"({info.file_size:,} bytes)\n"
            )

        out.write("\n## Source and Configuration Contents\n")

        total_chars = 0
        max_total = 1_000_000
        max_file = 30_000

        candidates = sorted(
            members,
            key=lambda x: (
                rank(x.filename),
                x.filename.lower()
            )
        )

        for info in candidates:
            path = PurePosixPath(info.filename)

            if path.suffix.lower() not in extensions:
                continue

            if total_chars >= max_total:
                break

            try:
                raw = archive.read(info)

                if len(raw) > 2_000_000:
                    continue

                content = raw.decode("utf-8")
            except (UnicodeDecodeError, RuntimeError, OSError):
                continue

            remaining = max_total - total_chars
            limit = min(max_file, remaining)

            if not content.strip():
                continue

            truncated = len(content) > limit
            if truncated:
                content = content[:limit]

            out.write(
                f"\n\n---\n\n## File: `{info.filename}`\n\n"
                f"```text\n{content}\n```\n"
            )

            if truncated:
                out.write(
                    "\n**NOTE: File content truncated; "
                    "remaining lines are not included.**\n"
                )

            total_chars += len(content)

        out.write(
            "\n\n## Bundle Limitations\n\n"
            "- Binary model artifacts and CSV datasets are not embedded.\n"
            "- Generated/build directories are excluded.\n"
            "- Large source files may be truncated.\n"
            "- The inventory lists files independently of content coverage.\n"
        )

print(f"Created: {output.resolve()}")
print(f"Size: {output.stat().st_size / 1024:.1f} KB")