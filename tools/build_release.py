from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tarfile
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def project_version() -> str:
    payload = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    return str(payload["project"]["version"])


def expected_tag_for_version(version: str) -> str:
    match = re.fullmatch(r"(\d+\.\d+\.\d+)a(\d+)", version)
    if not match:
        raise ValueError(f"Unsupported Alpha version format: {version}")
    return f"v{match.group(1)}-alpha.{match.group(2)}"


def git_text(*args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=check,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def release_source_files() -> list[Path]:
    output = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    ).stdout
    paths: list[Path] = []
    for raw_path in output.split(b"\0"):
        if not raw_path:
            continue
        relative = Path(raw_path.decode("utf-8"))
        if relative.parts and relative.parts[0] == "dist":
            continue
        if "__pycache__" in relative.parts or relative.suffix in {".pyc", ".pyo"}:
            continue
        candidate = ROOT / relative
        if candidate.is_file():
            paths.append(relative)
    return sorted(paths, key=lambda path: path.as_posix())


def build_source_archive(output_path: Path, version: str) -> None:
    prefix = Path(f"kol-signal-{version}")
    with tarfile.open(output_path, "w:gz") as archive:
        for relative in release_source_files():
            archive.add(
                ROOT / relative,
                arcname=(prefix / relative).as_posix(),
                recursive=False,
            )


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_release(output_dir: Path) -> dict[str, object]:
    version = project_version()
    expected_tag = expected_tag_for_version(version)
    output_dir.mkdir(parents=True, exist_ok=True)

    wheel_name = f"kol_signal-{version}-py3-none-any.whl"
    source_name = f"kol-signal-{version}-source.tar.gz"
    release_notes_name = "RELEASE_NOTES.md"
    for name in (wheel_name, source_name, release_notes_name, "SHA256SUMS", "release-manifest.json"):
        target = output_dir / name
        if target.exists():
            target.unlink()

    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "wheel",
            ".",
            "--no-deps",
            "--no-build-isolation",
            "--wheel-dir",
            str(output_dir),
        ],
        cwd=ROOT,
        check=True,
    )
    wheel_path = output_dir / wheel_name
    if not wheel_path.is_file():
        raise RuntimeError(f"Expected wheel was not created: {wheel_path}")

    source_path = output_dir / source_name
    build_source_archive(source_path, version)

    release_notes_source = (
        ROOT / "docs" / "releases" / f"{expected_tag}.md"
    )
    if not release_notes_source.is_file():
        raise RuntimeError(f"Missing release notes: {release_notes_source}")
    release_notes_path = output_dir / release_notes_name
    shutil.copyfile(release_notes_source, release_notes_path)

    checksum_targets = [wheel_path, source_path, release_notes_path]
    checksum_path = output_dir / "SHA256SUMS"
    checksum_path.write_text(
        "".join(f"{sha256(path)}  {path.name}\n" for path in checksum_targets),
        encoding="utf-8",
    )

    head_commit = git_text("rev-parse", "HEAD")
    tag_commit = git_text("rev-list", "-n", "1", expected_tag, check=False) or None
    dirty = bool(git_text("status", "--porcelain"))
    tag_points_to_head = tag_commit == head_commit
    source_matches_tag = tag_points_to_head and not dirty
    manifest = {
        "schema_version": 1,
        "package_version": version,
        "expected_git_tag": expected_tag,
        "head_commit": head_commit,
        "tag_commit": tag_commit,
        "git_dirty": dirty,
        "tag_points_to_head": tag_points_to_head,
        "source_matches_tag": source_matches_tag,
        "release_ready": source_matches_tag,
        "assets": [
            {
                "name": path.name,
                "sha256": sha256(path),
            }
            for path in checksum_targets
        ],
        "release_blockers": (
            []
            if source_matches_tag
            else [
                "The release source is not an exact clean match for the expected Git tag."
            ]
        ),
    }
    manifest_path = output_dir / "release-manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    for generated in (ROOT / "build", ROOT / "kol_signal.egg-info"):
        if generated.exists():
            shutil.rmtree(generated)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build local GitHub Release Candidate assets."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "dist",
        help="Release asset directory. Default: ./dist",
    )
    args = parser.parse_args()
    manifest = build_release(args.output.resolve())
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0 if manifest["release_ready"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
