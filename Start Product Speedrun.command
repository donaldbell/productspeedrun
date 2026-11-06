#!/bin/bash
# Double-click this file in Finder to start the Product Speedrun console.
# It stops any copy that's already running, gets the latest updates,
# starts the console and opens it in Chrome. Close this window to stop it.

# "yes" also opens Claude Code in this folder in a second Terminal window.
OPEN_CLAUDE_CODE="yes"

PORT=4321
cd "$(dirname "$0")" || exit 1
FOLDER="$(pwd)"

# Make sure Homebrew and nvm installs of Node are found when launched from Finder.
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
[ -s "$HOME/.nvm/nvm.sh" ] && . "$HOME/.nvm/nvm.sh" >/dev/null 2>&1

clear
echo ""
echo "  ▶ Product Speedrun"
echo "  ─────────────────"
echo ""

if ! command -v node >/dev/null 2>&1; then
  echo "  Node isn't installed. Get the LTS version from https://nodejs.org, then double-click this file again."
  echo ""
  read -r -p "  Press Return to close this window."
  exit 1
fi

# 1. Stop a copy that's already running.
if lsof -ti tcp:$PORT >/dev/null 2>&1; then
  echo "  Stopping the copy that was already running…"
  lsof -ti tcp:$PORT | xargs kill 2>/dev/null
  sleep 1
fi

# 2. Get the latest updates (keeps going if there's no internet).
#    Commits made on this Mac (Claude Code, the Publish buttons) are replayed on top of GitHub's,
#    and uncommitted changes are set aside and put back. If the two clash, nothing is changed.
echo "  Checking for updates…"
if git pull --rebase --autostash --quiet 2>/tmp/psr-pull.log; then
  echo "  Up to date."
  if [ -n "$(git log --oneline @{u}..HEAD 2>/dev/null)" ]; then
    if git push --quiet 2>>/tmp/psr-pull.log; then echo "  Sent this Mac's new commits to GitHub."; fi
  fi
else
  git rebase --abort >/dev/null 2>&1
  echo "  Couldn't update right now, so starting the version you have."
  echo "  (Details: $(grep -v '^$' /tmp/psr-pull.log | tail -1))"
  echo "  If this keeps happening, ask Claude: it's usually the same file changed here and on GitHub."
fi
echo ""

# 3. Open Chrome once the console is ready.
(
  for _ in $(seq 1 40); do
    curl -s -o /dev/null "http://localhost:$PORT/api/config" && break
    sleep 0.5
  done
  open -a "Google Chrome" "http://localhost:$PORT" 2>/dev/null || open "http://localhost:$PORT"
) &

# Optional: Claude Code in its own window, already in this folder.
if [ "$OPEN_CLAUDE_CODE" = "yes" ]; then
  osascript -e "tell application \"Terminal\" to do script \"cd '$FOLDER' && claude\"" >/dev/null 2>&1
fi

# Keep the Mac awake while the console runs, so Claude Code can keep working overnight
# (the screen may still turn off). Stops by itself when this window closes.
caffeinate -is -w $$ >/dev/null 2>&1 &

echo "  Leave this window open while you work. Close it (or press Control+C) to stop the console."
echo "  Your work is saved as you go, so stopping never loses anything."
node server.mjs
echo ""
read -r -p "  The console has stopped. Press Return to close this window."
