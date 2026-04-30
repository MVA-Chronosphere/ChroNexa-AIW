#!/bin/bash

echo "Downloading realistic character models..."

# Try direct GitHub URLs with simple loop
urls=(
  "https://raw.githubusercontent.com/mrdoob/three.js/master/examples/models/gltf/Michelle.glb"
  "https://raw.githubusercontent.com/mrdoob/three.js/master/examples/models/gltf/Partygirlv5.06.glb"
)

for url in "${urls[@]}"; do
  filename="${url##*/}"
  echo "Trying: $filename..."
  curl -L --connect-timeout 15 --max-time 30 -o "model_$filename" "$url" 2>/dev/null
  size=$(stat -f%z "model_$filename" 2>/dev/null || echo 0)
  if [ "$size" -gt 1000000 ]; then
    echo "  ✓ Downloaded: $size bytes"
    file "model_$filename"
  else
    echo "  ✗ Failed (size: $size)"
    rm -f "model_$filename"
  fi
done

echo ""
echo "Listing all downloaded models:"
ls -lh avatar*.glb model*.glb 2>/dev/null | grep -E "\.glb$"

