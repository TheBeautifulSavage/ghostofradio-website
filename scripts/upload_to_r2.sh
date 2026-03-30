#!/bin/bash
# Upload all local MP3s to Cloudflare R2 in parallel (8 workers)

export CLOUDFLARE_API_TOKEN="cfut_F7Gk8H3OrM2QQ34UoqpRfo3F3mHuNd222p2IMdm73b91416a"
export CLOUDFLARE_ACCOUNT_ID="dae784fdc17957e814046c3637ee10eb"
BUCKET="ghostofradio-audio"
AUDIO_DIR="/Users/mac1/Projects/ghostofradio/audio"
LOG="/Users/mac1/Projects/ghostofradio/scripts/logs/r2_upload.log"

mkdir -p "$(dirname $LOG)"
echo "Starting R2 upload at $(date)" | tee "$LOG"

# Get all MP3s
FILES=($(find "$AUDIO_DIR" -name "*.mp3" | sort))
TOTAL=${#FILES[@]}
echo "Total files: $TOTAL" | tee -a "$LOG"

upload_file() {
  local file="$1"
  local rel="${file#$AUDIO_DIR/}"  # e.g. sam-spade/chargogagog.mp3
  wrangler r2 object put "$BUCKET/$rel" \
    --file="$file" \
    --content-type="audio/mpeg" \
    --remote 2>/dev/null \
    && echo "✓ $rel" \
    || echo "✗ FAIL $rel"
}

export -f upload_file
export AUDIO_DIR BUCKET

# Run with 8 parallel workers
printf '%s\n' "${FILES[@]}" | xargs -P 8 -I {} bash -c 'upload_file "$@"' _ {} 2>&1 | tee -a "$LOG"

echo "" | tee -a "$LOG"
echo "Upload done at $(date)" | tee -a "$LOG"
echo "Total: $TOTAL files processed" | tee -a "$LOG"
