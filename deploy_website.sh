#!/usr/bin/env bash
#
# Publish the website in this repo (website/) to the live site (public_html).
#
# public_html is a separate copy of the site, not a link into this repo -
# committing and pushing website/ changes does NOT update the live site.
# This script does that last step.
#
# What it does:
#   1. Refuses to run if website/ has uncommitted changes (so what's live
#      always matches what's in git) - override with --allow-dirty.
#   2. Lists exactly which files would change.
#   3. Backs up each live file it is about to overwrite into
#      website_backups/<name>.bak-<timestamp>.
#   4. Copies the changed files over, then verifies the two folders match.
#
# It never deletes anything from public_html (cgi-bin, send_mail.php, and
# anything else that only exists on the server are left alone).
#
# Usage:
#   ./deploy_website.sh --dry-run      show what would change, touch nothing
#   ./deploy_website.sh                deploy
#   ./deploy_website.sh --allow-dirty  deploy even with uncommitted changes
#
# Paths can be overridden for testing:
#   PUBLIC_HTML=/some/dir BACKUP_DIR=/some/dir ./deploy_website.sh

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="$REPO_DIR/website"
DEST="${PUBLIC_HTML:-$HOME/public_html}"
BACKUP_DIR="${BACKUP_DIR:-$REPO_DIR/website_backups}"

DRY_RUN=0
ALLOW_DIRTY=0
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    --allow-dirty) ALLOW_DIRTY=1 ;;
    -h|--help) sed -n '2,/^set -euo/p' "$0" | sed '$d' | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "Unknown option: $arg (try --help)" >&2; exit 2 ;;
  esac
done

[ -d "$SRC" ] || { echo "ERROR: $SRC not found." >&2; exit 1; }
[ -d "$DEST" ] || { echo "ERROR: $DEST not found." >&2; exit 1; }

if [ "$ALLOW_DIRTY" -eq 0 ] && [ -n "$(git -C "$REPO_DIR" status --porcelain -- website)" ]; then
  echo "ERROR: website/ has uncommitted changes:" >&2
  git -C "$REPO_DIR" status --short -- website >&2
  echo "Commit them first, or re-run with --allow-dirty." >&2
  exit 1
fi

# Not deployed: git housekeeping and editor/backup leftovers.
EXCLUDES=(--exclude=.gitignore --exclude=.DS_Store --exclude='*.bak' --exclude='*.bak-*')

# -r recursive, -c compare by checksum (not mtime), -i itemize. No -p/-t/-o/-g:
# existing file permissions on the server are left as they are.
RSYNC_FLAGS=(-rci --no-perms --no-times --no-owner --no-group "${EXCLUDES[@]}")

# Lines look like ">fcst...... news.html" (changed) or ">f+++++++++ new.html".
CHANGES="$(rsync "${RSYNC_FLAGS[@]}" --dry-run --out-format='%i %n' "$SRC/" "$DEST/" | grep '^>f' || true)"

if [ -z "$CHANGES" ]; then
  echo "Nothing to deploy - $DEST already matches website/."
  exit 0
fi

echo "Files to deploy to $DEST:"
echo "$CHANGES" | while read -r flags name; do
  if [[ "$flags" == *"++++++++"* ]]; then echo "  new      $name"; else echo "  changed  $name"; fi
done

if [ "$DRY_RUN" -eq 1 ]; then
  echo "(dry run - nothing was changed)"
  exit 0
fi

STAMP="$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"
echo "$CHANGES" | while read -r flags name; do
  if [ -f "$DEST/$name" ]; then
    mkdir -p "$BACKUP_DIR/$(dirname "$name")"
    cp -p "$DEST/$name" "$BACKUP_DIR/$name.bak-$STAMP"
  fi
done
echo "Backed up overwritten live files to $BACKUP_DIR (*.bak-$STAMP)."

rsync "${RSYNC_FLAGS[@]}" "$SRC/" "$DEST/" >/dev/null

# Verify: anything still different means the copy did not take.
LEFTOVER="$(rsync "${RSYNC_FLAGS[@]}" --dry-run --out-format='%i %n' "$SRC/" "$DEST/" | grep '^>f' || true)"
if [ -n "$LEFTOVER" ]; then
  echo "ERROR: these files still differ after deploying:" >&2
  echo "$LEFTOVER" >&2
  exit 1
fi
echo "Deployed and verified. Hard-refresh the browser (Ctrl+F5) if a page looks unchanged."
