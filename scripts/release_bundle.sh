#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RELEASE_DIR="$ROOT_DIR/release"
FRONTEND_INDEX="$ROOT_DIR/frontend/dist/index.html"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
BUNDLE_NAME="ai-platform-square-hb-${TIMESTAMP}.tar.gz"
BUNDLE_PATH="$RELEASE_DIR/$BUNDLE_NAME"

if [ ! -f "$FRONTEND_INDEX" ]; then
  cat >&2 <<'EOF'
frontend/dist is missing.
Run 'make frontend-build' on the development machine before packaging a release bundle.
EOF
  exit 1
fi

mkdir -p "$RELEASE_DIR"

(
  cd "$ROOT_DIR"
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
