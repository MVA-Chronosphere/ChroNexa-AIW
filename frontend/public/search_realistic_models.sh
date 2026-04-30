#!/bin/bash

echo "Searching for more realistic female character models..."

# Create a more comprehensive search
MODEL_URLS=(
  "https://cdn.jsdelivr.net/npm/three@r128/examples/models/gltf/Michelle.glb"
  "https://cdn.jsdelivr.net/npm/three@r128/examples/models/gltf/Xbot.glb"
  "https://cdn.jsdelivr.net/npm/three@r128/examples/models/gltf/Partygirlv5.06.glb"
)

for i in "${!MODEL_URLS[@]}"; do
  url="${MODEL_URLS[$i]}"
  filename="candidate_$i.glb"
  echo "Trying: $url"
  if curl -L --connect-timeout 10 --max-time 20 -o "$filename" "$url" 2>/dev/null; then
    size=$(stat -f%z "$filename" 2>/dev/null || stat -c%s "$filename" 2>/dev/null)
    if [ "$size" -gt 1000000 ]; then
      echo "  ✓ Downloaded ($size bytes)"
    else
      echo "  ✗ File too small ($size bytes), likely error"
      rm -f "$filename"
    fi
  else
    echo "  ✗ Download failed"
    rm -f "$filename"
  fi
done

echo ""
echo "Checking downloaded files:"
file candidate_*.glb 2>/dev/null || echo "No valid files found"
ls -lh candidate_*.glb 2>/dev/null

