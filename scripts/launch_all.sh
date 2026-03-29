#!/bin/bash
# Ghost of Radio — Full Library Parallel Launcher
# Downloads from archive.org + generates pages using Ollama (zero API cost)

SCRIPT="/Users/mac1/Projects/ghostofradio/scripts/download_and_generate.py"
GEN="/Users/mac1/Projects/ghostofradio/scripts/generate_episodes.py"
LOG="/Users/mac1/Projects/ghostofradio/scripts/logs"
mkdir -p "$LOG"

echo "🎙️  Ghost of Radio — Full OTR Library Generator"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Models: qwen2.5:14b + llama3.2:3b (local, zero API cost)"

# Kill any existing workers
pkill -f "generate_episodes.py" 2>/dev/null
pkill -f "download_and_generate.py" 2>/dev/null
sleep 2

# ── Worker 1: Shadow (high quality, already 31 done) ──────────────────────
echo "▶ W1: The Shadow (203 eps) → qwen2.5:14b"
OLLAMA_MODEL_OVERRIDE=qwen2.5:14b python3 "$GEN" shadow \
  >> "$LOG/shadow.log" 2>&1 &

sleep 3

# ── Worker 2: Whistler + Gunsmoke ─────────────────────────────────────────
echo "▶ W2: Whistler (552) + Gunsmoke → llama3.2:3b"
OLLAMA_MODEL_OVERRIDE=llama3.2:3b python3 "$GEN" whistler \
  >> "$LOG/whistler.log" 2>&1 &

sleep 3

# ── Worker 3: CBS Mystery + Crime Classics ────────────────────────────────
echo "▶ W3: CBS Mystery (212) → llama3.2:3b"
OLLAMA_MODEL_OVERRIDE=llama3.2:3b python3 "$GEN" cbs-mystery \
  >> "$LOG/cbs-mystery.log" 2>&1 &

sleep 3

# ── Worker 4: Sherlock + Sounds of Darkness + Johnny Dollar ──────────────
echo "▶ W4: Sherlock + Sounds of Darkness + Johnny Dollar → qwen2.5:14b"
OLLAMA_MODEL_OVERRIDE=qwen2.5:14b python3 "$GEN" sherlock sounds-of-darkness \
  >> "$LOG/sherlock.log" 2>&1 &

sleep 3

# ── Worker 5: archive.org downloads — Suspense, Dragnet, Jack Benny ──────
echo "▶ W5: Suspense + Dragnet + Jack Benny (archive.org) → llama3.2:3b"
OLLAMA_MODEL_OVERRIDE=llama3.2:3b python3 "$SCRIPT" suspense dragnet jack-benny \
  >> "$LOG/archive1.log" 2>&1 &

sleep 3

# ── Worker 6: Escape, Inner Sanctum, X Minus One ─────────────────────────
echo "▶ W6: Escape + Inner Sanctum + X Minus One (archive.org) → llama3.2:3b"
OLLAMA_MODEL_OVERRIDE=llama3.2:3b python3 "$SCRIPT" escape inner-sanctum x-minus-one \
  >> "$LOG/archive2.log" 2>&1 &

sleep 3

# ── Worker 7: Lux Radio Theatre, Lone Ranger, Green Hornet ───────────────
echo "▶ W7: Lux Radio + Lone Ranger + Green Hornet (archive.org) → llama3.2:3b"
OLLAMA_MODEL_OVERRIDE=llama3.2:3b python3 "$SCRIPT" lux-radio-theatre lone-ranger green-hornet \
  >> "$LOG/archive3.log" 2>&1 &

sleep 3

# ── Worker 8: Sam Spade + Philip Marlowe + Richard Diamond ───────────────
echo "▶ W8: Sam Spade + Marlowe + Diamond → qwen2.5:14b"
OLLAMA_MODEL_OVERRIDE=qwen2.5:14b python3 "$SCRIPT" sam-spade philip-marlowe richard-diamond \
  >> "$LOG/archive4.log" 2>&1 &

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "8 workers running in parallel."
echo ""
echo "Monitor:"
echo "  tail -f $LOG/shadow.log"
echo "  tail -f $LOG/whistler.log"
echo "  watch -n 30 'find /Users/mac1/Projects/ghostofradio/blog -name \"*.html\" | wc -l'"
echo ""
echo "Progress check: find /Users/mac1/Projects/ghostofradio/blog -name '*.html' | wc -l"
