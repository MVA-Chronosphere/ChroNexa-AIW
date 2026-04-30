#!/bin/bash

# Try downloading a realistic female doctor model from various sources
echo "Searching for realistic female doctor avatar models..."

# Option 1: Try a direct realistic character from a GitHub repository
echo "Attempting Option 1: Realistic character from GitHub..."
curl -L --connect-timeout 10 -o avatar_doctor_v1.glb \
  "https://cdn.jsdelivr.net/gh/pmndrs/gltfjsx@v6.1.10/public/suzanne-armature.glb" 2>/dev/null && \
  echo "Downloaded from GitHub (Suzanne model)" || echo "GitHub source failed"

# Option 2: Try a realistic female avatar from a scanning model archive
echo "Attempting Option 2: Realistic scanned model..."
curl -L --connect-timeout 10 -o avatar_doctor_v2.glb \
  "https://raw.githubusercontent.com/mrdoob/three.js/master/examples/models/gltf/Xbot.glb" 2>/dev/null && \
  echo "Downloaded Xbot model" || echo "Xbot source failed"

# Option 3: Look for a realistic character model
echo "Attempting Option 3: Realistic LeePerrySmith character..."
curl -L --connect-timeout 10 -o avatar_doctor_v3.glb \
  "https://cdn.jsdelivr.net/npm/three@r128/examples/models/gltf/LeePerrySmith.glb" 2>/dev/null && \
  echo "Downloaded LeePerrySmith model" || echo "LeePerrySmith source failed"

# Option 4: Try the Soldier model (female character)
echo "Attempting Option 4: Soldier character..."
curl -L --connect-timeout 10 -o avatar_doctor_v4.glb \
  "https://cdn.jsdelivr.net/npm/three@r128/examples/models/gltf/Soldier.glb" 2>/dev/null && \
  echo "Downloaded Soldier model" || echo "Soldier source failed"

echo ""
echo "Files downloaded:"
ls -lh avatar_doctor_v*.glb 2>/dev/null || echo "No files downloaded"

