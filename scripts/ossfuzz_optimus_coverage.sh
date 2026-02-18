#!/usr/bin/env bash
set -euo pipefail

REMOTE_HOST=${REMOTE_HOST:-webkit@optimus}
REMOTE_ROOT=${REMOTE_ROOT:-/home/webkit/assimp}
OSSFUZZ_ROOT=${OSSFUZZ_ROOT:-$REMOTE_ROOT/oss-fuzz-test}
PROJECT_NAME=${PROJECT_NAME:-assimp}

RSYNC_EXCLUDES=(
  --exclude '.git'
  --exclude '.venv'
  --exclude '.lake'
  --exclude 'build'
  --exclude 'build_*'
  --exclude 'oss-fuzz-test'
)

sync_repo() {
  rsync -a --delete "${RSYNC_EXCLUDES[@]}" ./ "$REMOTE_HOST:$REMOTE_ROOT/"
}

sync_local_src() {
  ssh "$REMOTE_HOST" \
    "rsync -a --delete ${RSYNC_EXCLUDES[*]} $REMOTE_ROOT/ $OSSFUZZ_ROOT/projects/$PROJECT_NAME/local-src/"
}

sync_project_scripts() {
  ssh "$REMOTE_HOST" \
    "cp $REMOTE_ROOT/fuzz/ossfuzz/build.sh $OSSFUZZ_ROOT/projects/$PROJECT_NAME/build.sh && \
     [ ! -f $REMOTE_ROOT/fuzz/ossfuzz/run_tests.sh ] || \
     cp $REMOTE_ROOT/fuzz/ossfuzz/run_tests.sh $OSSFUZZ_ROOT/projects/$PROJECT_NAME/run_tests.sh"
}

kill_coverage_server() {
  ssh "$REMOTE_HOST" \
    "docker ps --format '{{.ID}} {{.Ports}}' | awk '/:8008->/{print \$1}' | xargs -r docker rm -f"
}

build_coverage_fuzzers() {
  ssh "$REMOTE_HOST" \
    "cd $OSSFUZZ_ROOT && python3 infra/helper.py build_fuzzers --sanitizer coverage $PROJECT_NAME"
}

extract_seed_corpora() {
  # --no-corpus-download skips BOTH GCS download AND seed zip extraction.
  # We must manually extract seed zips into corpus dirs before running coverage.
  ssh "$REMOTE_HOST" bash -s -- "$OSSFUZZ_ROOT" "$PROJECT_NAME" <<'EXTRACT_EOF'
    OSSFUZZ_ROOT="$1"
    PROJECT_NAME="$2"
    BUILD_OUT="$OSSFUZZ_ROOT/build/out/$PROJECT_NAME"
    CORPUS_DIR="$OSSFUZZ_ROOT/build/out/corpus/$PROJECT_NAME"
    mkdir -p "$CORPUS_DIR"
    for zip in "$BUILD_OUT"/*_seed_corpus.zip; do
      [ -f "$zip" ] || continue
      fuzzer=$(basename "$zip" _seed_corpus.zip)
      dest="$CORPUS_DIR/$fuzzer"
      rm -rf "$dest"
      mkdir -p "$dest"
      unzip -q -o "$zip" -d "$dest" 2>/dev/null || true
      # Flatten subdirectories (fuzzers only read top-level files)
      python3 -c "
import os, shutil
corpus = '$dest'
for root, dirs, files in os.walk(corpus):
    if root == corpus:
        continue
    for f in files:
        src = os.path.join(root, f)
        dst = os.path.join(corpus, f)
        if os.path.exists(dst):
            dst = os.path.join(corpus, os.path.basename(root) + '_' + f)
        try:
            shutil.move(src, dst)
        except:
            pass
for root, dirs, files in os.walk(corpus, topdown=False):
    if root != corpus:
        try:
            os.rmdir(root)
        except:
            pass
" 2>/dev/null || true
      count=$(find "$dest" -maxdepth 1 -type f | wc -l)
      echo "Extracted $count files -> $fuzzer"
    done
EXTRACT_EOF
}

run_coverage() {
  ssh "$REMOTE_HOST" \
    "cd $OSSFUZZ_ROOT && python3 infra/helper.py coverage --no-corpus-download --no-serve $PROJECT_NAME"
}

main() {
  sync_repo
  sync_local_src
  sync_project_scripts
  kill_coverage_server
  build_coverage_fuzzers
  extract_seed_corpora
  run_coverage || true
  kill_coverage_server
}

main "$@"
