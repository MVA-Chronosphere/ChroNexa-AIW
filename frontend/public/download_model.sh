#!/bin/bash
# Download a free female character model
curl -L -o avatar.glb "https://cdn.jsdelivr.net/npm/three@r128/examples/models/gltf/Soldier.glb"
echo "Download completed"
ls -lh avatar.glb 2>/dev/null && echo "File exists" || echo "File not found"
