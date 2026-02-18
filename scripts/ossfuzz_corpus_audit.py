#!/usr/bin/env python3
import argparse
from collections import Counter
from pathlib import Path
import zipfile


SUSPICIOUS_EXTS = {"png", "jpg", "jpeg", "gif", "txt", "md", "pdf", "html", "htm"}


def audit_zip(zip_path: Path, top_n: int, big_threshold: int):
    with zipfile.ZipFile(zip_path) as zf:
        infos = [info for info in zf.infolist() if not info.is_dir()]
    total_files = len(infos)
    total_bytes = sum(info.file_size for info in infos)
    ext_counts = Counter()
    dir_sizes = Counter()
    dir_counts = Counter()
    ref_count = 0
    screenshot_count = 0
    big_count = 0
    for info in infos:
        name = info.filename
        name_lower = name.lower()
        ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
        ext_counts[ext] += 1
        top_dir = name.split("/", 1)[0]
        dir_sizes[top_dir] += info.file_size
        dir_counts[top_dir] += 1
        if "/ref/" in name_lower or name_lower.startswith("ref/"):
            ref_count += 1
        if "/screenshots/" in name_lower or "screenshot" in name_lower:
            screenshot_count += 1
        if info.file_size >= big_threshold:
            big_count += 1
    largest = sorted(infos, key=lambda i: i.file_size, reverse=True)[:top_n]
    return (
        total_files,
        total_bytes,
        ext_counts,
        dir_sizes,
        dir_counts,
        largest,
        ref_count,
        screenshot_count,
        big_count,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit OSS-Fuzz seed corpus zips.")
    parser.add_argument(
        "out_dir",
        nargs="?",
        default="oss-fuzz-test/build/out/assimp",
        help="Path to OSS-Fuzz out directory (default: oss-fuzz-test/build/out/assimp).",
    )
    parser.add_argument("--top", type=int, default=5, help="Top N largest files to show.")
    parser.add_argument(
        "--top-dirs",
        type=int,
        default=5,
        help="Top N largest top-level directories to show.",
    )
    parser.add_argument(
        "--big-threshold",
        type=int,
        default=1_000_000,
        help="Size threshold (bytes) to count large entries.",
    )
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    if not out_dir.is_dir():
        print(f"Missing out dir: {out_dir}")
        return 2

    zips = sorted(out_dir.glob("*_seed_corpus.zip"))
    if not zips:
        print(f"No seed corpora found under {out_dir}")
        return 1

    summaries = []
    for zip_path in zips:
        (
            total_files,
            total_bytes,
            ext_counts,
            dir_sizes,
            dir_counts,
            largest,
            ref_count,
            screenshot_count,
            big_count,
        ) = audit_zip(zip_path, args.top, args.big_threshold)
        summaries.append(
            (
                total_bytes,
                zip_path,
                total_files,
                ext_counts,
                dir_sizes,
                dir_counts,
                largest,
                ref_count,
                screenshot_count,
                big_count,
            )
        )

    for (
        total_bytes,
        zip_path,
        total_files,
        ext_counts,
        dir_sizes,
        dir_counts,
        largest,
        ref_count,
        screenshot_count,
        big_count,
    ) in sorted(
        summaries, key=lambda row: row[0], reverse=True
    ):
        print(
            f"{zip_path.name}: {total_files} files, {total_bytes/1024/1024:.1f} MB"
            f", ref={ref_count}, screenshots={screenshot_count}, >={args.big_threshold}B={big_count}"
        )
        suspicious = {ext: ext_counts[ext] for ext in SUSPICIOUS_EXTS if ext in ext_counts}
        if suspicious:
            items = ", ".join(f"{ext}={count}" for ext, count in sorted(suspicious.items()))
            print(f"  suspicious: {items}")
        top_dirs = sorted(dir_sizes.items(), key=lambda kv: kv[1], reverse=True)[: args.top_dirs]
        if top_dirs:
            items = ", ".join(
                f"{name}={size/1024/1024:.1f}MB/{dir_counts[name]}"
                for name, size in top_dirs
            )
            print(f"  top dirs: {items}")
        print("  largest:")
        for info in largest:
            print(f"    {info.file_size} {info.filename}")
        print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
