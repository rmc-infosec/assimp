#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="$ROOT_DIR/oss-fuzz-test/build/out/assimp"
CORPUS_DIR="$ROOT_DIR/oss-fuzz-test/build/corpus/assimp"

if [[ ! -d "$OUT_DIR" ]]; then
  echo "Missing oss-fuzz out directory: $OUT_DIR" >&2
  exit 1
fi

mkdir -p "$CORPUS_DIR"

shopt -s nullglob
for zip_path in "$OUT_DIR"/*_seed_corpus.zip; do
  zip_name="$(basename "$zip_path")"
  fuzzer_name="${zip_name%_seed_corpus.zip}"
  dest_dir="$CORPUS_DIR/$fuzzer_name"
  mkdir -p "$dest_dir"
  if [[ ! -w "$dest_dir" ]]; then
    echo "Skipping $fuzzer_name (corpus dir not writable): $dest_dir" >&2
    continue
  fi
  unzip -q -n "$zip_path" -d "$dest_dir"
done
