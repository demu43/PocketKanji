#!/bin/zsh

set -u
unsetopt BG_NICE

SCRIPT_DIR=${0:A:h}
APP_FILE="$SCRIPT_DIR/PocketKanji.html"
PYTHON_BIN=$(command -v python3 2>/dev/null || true)
PORT=""
NO_BROWSER=0

if [[ "${1:-}" == "--no-browser" ]]; then
  NO_BROWSER=1
fi

if [[ ! -f "$APP_FILE" ]]; then
  print -u2 "Errore: PocketKanji.html non trovato nella cartella del programma."
  read -r "?Premi Invio per chiudere."
  exit 1
fi

if [[ -z "$PYTHON_BIN" ]]; then
  print -u2 "Errore: Python 3 non è disponibile su questo Mac."
  print -u2 "Installa Python 3 oppure apri PocketKanji.html direttamente nel browser."
  print -u2 "L'avvio diretto usa però un archivio browser diverso da localhost."
  read -r "?Premi Invio per chiudere."
  exit 1
fi

for candidate in {8765..8775}; do
  URL="http://127.0.0.1:${candidate}/PocketKanji.html"

  if /usr/bin/curl --silent --fail --max-time 1 "$URL" 2>/dev/null | /usr/bin/grep -q '<title>PocketKanji'; then
    if (( NO_BROWSER == 0 )); then
      /usr/bin/open "$URL"
    fi
    print "PocketKanji era già avviato: $URL"
    exit 0
  fi

  if ! /usr/sbin/lsof -nP -iTCP:"$candidate" -sTCP:LISTEN >/dev/null 2>&1; then
    PORT="$candidate"
    break
  fi
done

if [[ -z "$PORT" ]]; then
  print -u2 "Errore: le porte locali 8765-8775 sono occupate."
  read -r "?Premi Invio per chiudere."
  exit 1
fi

URL="http://127.0.0.1:${PORT}/PocketKanji.html"
LOG_FILE="${TMPDIR:-/tmp}/PocketKanji-server-${PORT}.log"

cd "$SCRIPT_DIR" || exit 1
"$PYTHON_BIN" -m http.server "$PORT" --bind 127.0.0.1 >"$LOG_FILE" 2>&1 &
SERVER_PID=$!

stop_server() {
  if kill -0 "$SERVER_PID" >/dev/null 2>&1; then
    kill "$SERVER_PID" >/dev/null 2>&1 || true
  fi
}
trap stop_server EXIT INT TERM

for attempt in {1..20}; do
  if /usr/bin/curl --silent --fail --max-time 1 "$URL" >/dev/null 2>&1; then
    if (( NO_BROWSER == 0 )); then
      /usr/bin/open "$URL"
    fi
    print "PocketKanji avviato: $URL"
    print "Lascia aperta questa finestra. Per fermare il servizio premi Ctrl+C."
    print "Log tecnico: $LOG_FILE"
    wait "$SERVER_PID"
    exit $?
  fi
  /bin/sleep 0.1
done

print -u2 "Errore: il server locale non si è avviato."
print -u2 "Controlla il log: $LOG_FILE"
exit 1
