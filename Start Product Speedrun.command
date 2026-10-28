#!/bin/bash
# Double-click this file in Finder to start the Product Speedrun console.
# It stops any copy that's already running, gets the latest updates,
# starts the console and opens it in Chrome. Close this window to stop it.

# Set to "yes" to also open Claude Code in this folder in a second Terminal window.
OPEN_CLAUDE_CODE="no"

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
echo "  Checking for updates…"
if git pull --ff-only --quiet 2>/tmp/psr-pull.log; then
  echo "  Up to date."
else
  echo "  Couldn't update right now, so starting the version you have."
  echo "  (Details: $(tail -1 /tmp/psr-pull.log))"
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

echo "  Leave this window open while you work. Close it (or press Control+C) to stop the console."
echo "  Your work is saved as you go, so stopping never loses anything."
node server.mjs
echo ""
read -r -p "  The console has stopped. Press Return to close this window."
