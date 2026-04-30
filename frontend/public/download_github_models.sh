#!/bin/bash

echo "Downloading realistic character models from GitHub..."

# Direct GitHub raw content URLs for Three.js models
declare -A MODELS=(
  ["xbot"]="https://raw.githubusercontent.com/mrdoob/three.js/master/examples/models/gltf/Xbot.glb"
  ["michelle"]="https://raw.githubusercontent.com/mrdoob/three.js/master/examples/models/gltf/Michelle.glb"
  ["partygirlv5"]="https://raw.githubusercontent.com/mrdoob/three.js/master/examples/models/gltf/Partygirlv5.06.glb"
)

for name in "${!MODELS[@]}"; do
  url="${MODELS[$name]}"
  filename="model_${name}.glb"
  echo ""
  echo "Downloading: $name from GitHub..."
  if curl -L --connect-timeout 15 --max-time 30 -o "$filename" "$url" 2>/dev/null; then
    size=$(stat -f%z "$filename" 2>/dev/null)
    if [ "$size" -gt 1000000 ]; then
      echo "  ✓ Success: $filename ($size bytes)"
      file "$filename" 2>/dev/null
    else
      echo "  ✗ File too small: $size bytes (likely error response)"
      rm -f "$filename"
    fi
  else
    echo "  ✗ Download failed"
    rm -f "$filename"
  fi
done

echo ""
echo "Final files in directory:"
ls -lh avatar*.glb model_*.glb 2>/dev/null | tail -10

