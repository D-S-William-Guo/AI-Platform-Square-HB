#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RELEASE_DIR="$ROOT_DIR/release"
FRONTEND_INDEX="$ROOT_DIR/frontend/dist/index.html"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
BUNDLE_NAME="ai-platform-square-hb-${TIMESTAMP}.tar.gz"
BUNDLE_PATH="$RELEASE_DIR/$BUNDLE_NAME"
STAGING_DIR="$(mktemp -d)"

cleanup() {
  rm -rf "$STAGING_DIR"
}

trap cleanup EXIT

if [ ! -f "$FRONTEND_INDEX" ]; then
  cat >&2 <<'EOF'
frontend/dist is missing.
Run 'make frontend-build' on the development machine before packaging a release bundle.
EOF
  exit 1
fi

mkdir -p "$RELEASE_DIR"

rsync -a \
  --exclude='.env' \
  --exclude='.pytest_cache/' \
  --exclude='__pycache__/' \
  --exclude='*.pyc' \
  --exclude='*.egg-info/' \
  --exclude='static/uploads/*' \
  --exclude='static/images/*' \
  "$ROOT_DIR/backend/" "$STAGING_DIR/backend/"

mkdir -p "$STAGING_DIR/frontend"
rsync -a "$ROOT_DIR/frontend/dist/" "$STAGING_DIR/frontend/dist/"
rsync -a "$ROOT_DIR/scripts/" "$STAGING_DIR/scripts/"
rsync -a "$ROOT_DIR/docs/" "$STAGING_DIR/docs/"
cp "$ROOT_DIR/Makefile" "$ROOT_DIR/README.md" "$ROOT_DIR/docker-compose.yml" "$ROOT_DIR/.env.example" "$STAGING_DIR/"

(
  cd "$STAGING_DIR"
  tar -czf "$BUNDLE_PATH" \
    backend \
    frontend/dist \
    scripts \
    docs \
    Makefile \
    README.md \
    docker-compose.yml \
    .env.example
)

echo "Created release bundle: $BUNDLE_PATH"
