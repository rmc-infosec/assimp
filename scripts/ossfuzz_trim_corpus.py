#!/usr/bin/env python3
import argparse
import shutil
import tempfile
from collections import Counter, defaultdict
from pathlib import Path
import zipfile


DEFAULT_DROP_EXTS = {
    "png",
    "jpg",
    "jpeg",
    "gif",
    "bmp",
    "tga",
    "tif",
    "tiff",
    "dds",
    "psd",
    "mtl",
    "txt",
    "md",
    "pdf",
    "html",
    "htm",
}


def should_drop(
    name: str,
    size: int,
    drop_exts: set,
    keep_exts: set,
    drop_paths: list,
    max_size: int | None,
):
    lower = name.lower()
    for pat in drop_paths:
        if pat in lower:
            return True, "path"
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    if keep_exts:
        if ext not in keep_exts:
            return True, "ext"
    elif ext in drop_exts:
        return True, "ext"
    if max_size is not None and size > max_size:
        return True, "size"
    return False, ""


def iter_zip_paths(root: Path, pattern: str):
    if root.is_file():
        return [root]
    if not root.is_dir():
        return []
    return sorted(root.glob(pattern))


def trim_zip(zip_path: Path, args) -> dict:
    drop_exts = set(ext.lower().lstrip(".") for ext in args.drop_ext)
    keep_exts = set(ext.lower().lstrip(".") for ext in args.keep_ext)
    drop_paths = [pat.lower() for pat in args.drop_path]
    max_size = args.max_size if args.max_size > 0 else None

    kept = 0
    dropped = 0
    dropped_by_reason = Counter()
    dropped_by_ext = Counter()
    dropped_by_dir = Counter()
    kept_bytes = 0
    dropped_bytes = 0

    with zipfile.ZipFile(zip_path) as zin:
        infos = [info for info in zin.infolist() if not info.is_dir()]
        if args.dry_run:
            for info in infos:
                drop, reason = should_drop(
                    info.filename,
                    info.file_size,
                    drop_exts,
                    keep_exts,
                    drop_paths,
                    max_size,
                )
                if drop:
                    dropped += 1
                    dropped_bytes += info.file_size
                    dropped_by_reason[reason] += 1
                    ext = info.filename.rsplit(".", 1)[-1].lower() if "." in info.filename else ""
                    dropped_by_ext[ext] += 1
                    top_dir = info.filename.split("/", 1)[0]
                    dropped_by_dir[top_dir] += 1
                else:
                    kept += 1
                    kept_bytes += info.file_size
            return {
                "kept": kept,
                "dropped": dropped,
                "kept_bytes": kept_bytes,
                "dropped_bytes": dropped_bytes,
                "dropped_by_reason": dropped_by_reason,
                "dropped_by_ext": dropped_by_ext,
                "dropped_by_dir": dropped_by_dir,
            }

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_zip = Path(tmpdir) / zip_path.name
            with zipfile.ZipFile(tmp_zip, "w", compression=zipfile.ZIP_DEFLATED) as zout:
                for info in infos:
                    drop, reason = should_drop(
                        info.filename,
                        info.file_size,
                        drop_exts,
                        keep_exts,
                        drop_paths,
                        max_size,
                    )
                    if drop:
                        dropped += 1
                        dropped_bytes += info.file_size
                        dropped_by_reason[reason] += 1
                        ext = (
                            info.filename.rsplit(".", 1)[-1].lower()
                            if "." in info.filename
                            else ""
                        )
                        dropped_by_ext[ext] += 1
                        top_dir = info.filename.split("/", 1)[0]
                        dropped_by_dir[top_dir] += 1
                        continue
                    kept += 1
                    kept_bytes += info.file_size
                    with zin.open(info) as src, zout.open(info.filename, "w") as dst:
                        shutil.copyfileobj(src, dst)

            if args.in_place:
                backup = zip_path.with_suffix(zip_path.suffix + args.backup_suffix)
                if backup.exists():
                    backup.unlink()
                zip_path.rename(backup)
                tmp_zip.replace(zip_path)
            else:
                out_path = zip_path.with_name(zip_path.stem + args.out_suffix + zip_path.suffix)
                if out_path.exists():
                    out_path.unlink()
                tmp_zip.replace(out_path)

    return {
        "kept": kept,
        "dropped": dropped,
        "kept_bytes": kept_bytes,
        "dropped_bytes": dropped_bytes,
        "dropped_by_reason": dropped_by_reason,
        "dropped_by_ext": dropped_by_ext,
        "dropped_by_dir": dropped_by_dir,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Trim OSS-Fuzz seed corpus zips.")
    parser.add_argument(
        "path",
        nargs="?",
        default="oss-fuzz-test/build/out/assimp",
        help="Zip file or directory to scan (default: oss-fuzz-test/build/out/assimp).",
    )
    parser.add_argument(
        "--pattern",
        default="*_seed_corpus.zip",
        help="Glob pattern when path is a directory.",
    )
    parser.add_argument(
        "--drop-ext",
        action="append",
        default=sorted(DEFAULT_DROP_EXTS),
        help="Extensions to drop (repeatable).",
    )
    parser.add_argument(
        "--keep-ext",
        action="append",
        default=[],
        help="If set, only these extensions are kept (repeatable).",
    )
    parser.add_argument(
        "--drop-path",
        action="append",
        default=[
            "/ref/",
            "ref/",
            "/screenshots/",
            "screenshots/",
            "screenshot",
            "/invalid/",
            "invalid/",
        ],
        help="Drop files containing these path substrings (case-insensitive).",
    )
    parser.add_argument(
        "--max-size",
        type=int,
        default=0,
        help="Drop files larger than this many bytes (0 disables).",
    )
    parser.add_argument(
        "--in-place",
        action="store_true",
        help="Rewrite the zip in-place (backup is kept).",
    )
    parser.add_argument(
        "--backup-suffix",
        default=".bak",
        help="Suffix for backup when --in-place is used.",
    )
    parser.add_argument(
        "--out-suffix",
        default=".trimmed",
        help="Suffix for output zip when not in-place.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Only report changes.")
    args = parser.parse_args()

    path = Path(args.path)
    zip_paths = iter_zip_paths(path, args.pattern)
    if not zip_paths:
        print(f"No zip files found under {path}")
        return 1

    for zip_path in zip_paths:
        stats = trim_zip(zip_path, args)
        kept = stats["kept"]
        dropped = stats["dropped"]
        kept_mb = stats["kept_bytes"] / 1024 / 1024
        dropped_mb = stats["dropped_bytes"] / 1024 / 1024
        print(
            f"{zip_path.name}: kept {kept} ({kept_mb:.1f} MB), "
            f"dropped {dropped} ({dropped_mb:.1f} MB)"
        )
        reasons = ", ".join(
            f"{k}={v}" for k, v in stats["dropped_by_reason"].most_common()
        )
        if reasons:
            print(f"  dropped by reason: {reasons}")
        top_exts = ", ".join(
            f"{k or '(none)'}={v}" for k, v in stats["dropped_by_ext"].most_common(8)
        )
        if top_exts:
            print(f"  dropped by ext: {top_exts}")
        top_dirs = ", ".join(
            f"{k}={v}" for k, v in stats["dropped_by_dir"].most_common(8)
        )
        if top_dirs:
            print(f"  dropped by dir: {top_dirs}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
