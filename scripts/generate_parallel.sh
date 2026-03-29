#!/bin/bash
# Ghost of Radio — Parallel Episode Generator
# Runs multiple show generators simultaneously

SCRIPT="/Users/mac1/Projects/ghostofradio/scripts/generate_episodes.py"
LOG_DIR="/Users/mac1/Projects/ghostofradio/scripts/logs"
mkdir -p "$LOG_DIR"

echo "🎙️  Ghost of Radio — Parallel Generator Starting"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Kill existing generators
pkill -f "generate_episodes.py" 2>/dev/null
sleep 2

# Worker 1: Shadow (203 eps) — qwen2.5:14b (already running, high quality)
echo "▶ Worker 1: The Shadow → qwen2.5:14b"
OLLAMA_MODEL_OVERRIDE=qwen2.5:14b python3 "$SCRIPT" shadow \
  >> "$LOG_DIR/shadow.log" 2>&1 &
PID1=$!
echo "  PID: $PID1"

sleep 5  # stagger start to avoid git conflicts

# Worker 2: Whistler (552 eps) — llama3.2:3b (faster, lower VRAM)  
echo "▶ Worker 2: The Whistler → llama3.2:3b"
OLLAMA_MODEL_OVERRIDE=llama3.2:3b python3 "$SCRIPT" whistler \
  >> "$LOG_DIR/whistler.log" 2>&1 &
PID2=$!
echo "  PID: $PID2"

sleep 5

# Worker 3: CBS Mystery (212 eps) — llama3.2:3b
echo "▶ Worker 3: CBS Mystery → llama3.2:3b"
OLLAMA_MODEL_OVERRIDE=llama3.2:3b python3 "$SCRIPT" cbs-mystery \
  >> "$LOG_DIR/cbs-mystery.log" 2>&1 &
PID3=$!
echo "  PID: $PID3"

sleep 5

# Worker 4: Sherlock (52 eps) + Sounds of Darkness (73 eps) — qwen2.5:14b
echo "▶ Worker 4: Sherlock + Sounds of Darkness → qwen2.5:14b"
OLLAMA_MODEL_OVERRIDE=qwen2.5:14b python3 "$SCRIPT" sherlock sounds-of-darkness \
  >> "$LOG_DIR/sherlock.log" 2>&1 &
PID4=$!
echo "  PID: $PID4"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "All workers running. Monitor with:"
echo "  tail -f $LOG_DIR/shadow.log"
echo "  tail -f $LOG_DIR/whistler.log"
echo "  tail -f $LOG_DIR/cbs-mystery.log"  
echo "  tail -f $LOG_DIR/sherlock.log"
echo ""
echo "Check progress: ls /Users/mac1/Projects/ghostofradio/blog/*/ | wc -l"
echo ""

# Wait for all and report
wait $PID1 $PID2 $PID3 $PID4
echo "✅ All generators complete!"
