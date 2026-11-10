#!/bin/bash
# Pull the latest scripts + recording guide onto the laptop (no git needed).
# Usage (in Terminal):  bash ~/RobloxTown/tools/laptop/sync.sh
set -e
BASE="https://raw.githubusercontent.com/MielJhan0323/RobloxTown/claude/clever-maxwell-t5glbr"
DIR="$HOME/RobloxTown"
mkdir -p "$DIR/scripts" "$DIR/tools/laptop" "$DIR/raw"
get() { curl -fsSL "$BASE/$1" -o "$DIR/$1" && echo "  got $1"; }
echo "Syncing from GitHub..."
get CLAUDE.md
get tools/laptop/RECORDING.md
get tools/laptop/sync.sh
get tools/laptop/StoryKit.lua
get scripts/INDEX.md
for slug in $(grep -E '^\| [a-z0-9-]+ \|' "$DIR/scripts/INDEX.md" | awk -F'|' '{gsub(/ /,"",$2); print $2}'); do
  get "scripts/$slug.md"
  curl -fsSL "$BASE/scripts/$slug.setup.md" -o "$DIR/scripts/$slug.setup.md" 2>/dev/null && echo "  got scripts/$slug.setup.md" || rm -f "$DIR/scripts/$slug.setup.md"
  mkdir -p "$DIR/raw/$slug"
done
echo "Done. Stories:"; grep -E '^\| [a-z0-9-]+ \|' "$DIR/scripts/INDEX.md"
