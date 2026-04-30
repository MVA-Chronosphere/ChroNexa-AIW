#!/bin/bash

# Script to verify if a GLB model has blend shapes/morph targets
# Usage: ./verify_model.sh model.glb

set -e

if [ -z "$1" ]; then
    echo "Usage: ./verify_model.sh <model.glb>"
    echo ""
    echo "Example:"
    echo "  ./verify_model.sh frontend/public/my_avatar.glb"
    exit 1
fi

MODEL_FILE="$1"

if [ ! -f "$MODEL_FILE" ]; then
    echo "ERROR: File not found: $MODEL_FILE"
    exit 1
fi

echo "================================"
echo "3D Model Blend Shapes Verification"
echo "================================"
echo ""
echo "File: $MODEL_FILE"
echo "Size: $(du -h "$MODEL_FILE" | cut -f1)"
echo ""

# Check if gltf-pipeline is installed
if ! command -v gltf-pipeline &> /dev/null; then
    echo "Installing gltf-pipeline globally..."
    npm install -g gltf-pipeline
fi

echo "Analyzing model..."
echo ""

# Create temp directory
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

# Convert GLB to GLTF for inspection (gltf-pipeline extracts to JSON)
gltf-pipeline -i "$MODEL_FILE" -o "$TEMP_DIR/model.glb" >/dev/null 2>&1 || true

# Alternative: use node to inspect JSON
node << 'EOF'
const fs = require('fs');
const zlib = require('zlib');
const path = require('path');

try {
    const modelPath = process.argv[1];
    const data = fs.readFileSync(modelPath);
    
    // GLB file structure: 12 byte header + chunks
    // Read JSON chunk (first chunk after header)
    let offset = 12; // Skip header
    
    // First chunk size (little-endian)
    const chunkSize = data.readUInt32LE(offset);
    const chunkType = data.toString('ascii', offset + 4, offset + 8);
    
    if (chunkType === 'JSON') {
        const jsonData = data.toString('utf8', offset + 8, offset + 8 + chunkSize);
        const gltf = JSON.parse(jsonData);
        
        console.log('✓ Valid GLB format\n');
        
        // Check for blend shapes
        let morphTargetCount = 0;
        let meshesWithMorphs = 0;
        const morphTargetNames = new Set();
        
        if (gltf.meshes) {
            gltf.meshes.forEach((mesh, idx) => {
                if (mesh.primitives) {
                    mesh.primitives.forEach(prim => {
                        if (prim.targets && prim.targets.length > 0) {
                            meshesWithMorphs++;
                            morphTargetCount += prim.targets.length;
                            
                            // Try to get target names from accessories
                            if (gltf.meshes[idx].name) {
                                morphTargetNames.add(gltf.meshes[idx].name);
                            }
                        }
                    });
                }
            });
        }
        
        console.log('GEOMETRY INFORMATION:');
        console.log('  Meshes: ' + (gltf.meshes ? gltf.meshes.length : 0));
        console.log('  Nodes: ' + (gltf.nodes ? gltf.nodes.length : 0));
        console.log('  Animations: ' + (gltf.animations ? gltf.animations.length : 0));
        
        console.log('\nBLEND SHAPES (MORPH TARGETS):');
        if (morphTargetCount > 0) {
            console.log('  ✅ FOUND: ' + morphTargetCount + ' morph targets');
            console.log('  Meshes with blend shapes: ' + meshesWithMorphs);
            console.log('  This model is COMPATIBLE with lip sync!');
        } else {
            console.log('  ❌ NOT FOUND: No morph targets detected');
            console.log('  This model CANNOT be used for lip sync animation');
        }
        
        // List animations
        if (gltf.animations && gltf.animations.length > 0) {
            console.log('\nANIMATIONS:');
            gltf.animations.forEach((anim, idx) => {
                console.log('  [' + idx + '] ' + (anim.name || 'Animation ' + idx));
            });
        }
        
        // Check for skeleton/armature
        if (gltf.skins && gltf.skins.length > 0) {
            console.log('\nSKELETON:');
            console.log('  ✅ Has armature/skeleton (' + gltf.skins.length + ' skin(s))');
        }
        
    }
} catch (err) {
    console.error('Error analyzing GLB: ' + err.message);
    process.exit(1);
}

EOF "$MODEL_FILE"

echo ""
echo "================================"
echo "Result Summary:"
echo "================================"
echo ""
echo "If model shows '✅ FOUND: X morph targets', it's ready for:"
echo "  - Lip sync animation with Rhubarb CLI"
echo "  - Blend shape manipulation in Three.js"
echo "  - Real-time audio-driven animation"
echo ""
echo "If model shows '❌ NOT FOUND', choose a different model."
echo ""
