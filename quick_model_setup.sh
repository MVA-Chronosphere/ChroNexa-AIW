#!/bin/bash

# Quick-Start Model Download & Integration for ChroNexa
# This script helps download, verify, and integrate a 3D model with blend shapes

set -e

WORKSPACE_DIR="/Users/chiefaiofficer/ChroNexa-AIW"
MODEL_NAME="${1:-doctor_avatar}"

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  ChroNexa Avatar - Quick-Start Model Integration              ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "This script will guide you through downloading and integrating"
echo "a 3D character model with blend shapes for lip sync animation."
echo ""

# Function to download model from URL
download_model() {
    local url="$1"
    local output="$2"
    
    echo "⏳ Downloading model..."
    if command -v curl &> /dev/null; then
        curl -L "$url" -o "$output"
    elif command -v wget &> /dev/null; then
        wget "$url" -O "$output"
    else
        echo "❌ Neither curl nor wget found"
        return 1
    fi
    
    echo "✅ Downloaded: $output"
}

# Step 1: Show recommended models
echo "STEP 1: Choose a Model"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Popular models with blend shapes (from Sketchfab):"
echo ""
echo "1. Scifi Girl v.01"
echo "   URL: https://sketchfab.com/3d-models/scifi-girl-v01-96340701c2ed4d37851c7d9109eee9c0"
echo "   Download GLB, then use: ./quick_model_setup.sh model.glb"
echo ""
echo "2. Other Sketchfab models"
echo "   Search: https://sketchfab.com/search?type=models&downloadable=true"
echo "   Tips: Look for 'rigged', 'animated', 'facial'"
echo ""
echo "3. Mixamo Characters (Recommended)"
echo "   URL: https://www.mixamo.com"
echo "   Need Adobe account (free)"
echo "   Download as: FBX + Blend Shapes"
echo "   Then convert: FBX → GLB using Blender"
echo ""

if [ -n "$1" ] && [ -f "$1" ]; then
    MODEL_FILE="$1"
    echo ""
    echo "STEP 2: Verify Model Has Blend Shapes"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    # Install gltf-pipeline if needed
    if ! command -v gltf-pipeline &> /dev/null; then
        echo "📦 Installing gltf-pipeline..."
        npm install -g gltf-pipeline >/dev/null 2>&1
    fi
    
    # Verify model
    echo "Analyzing: $MODEL_FILE"
    gltf-pipeline -i "$MODEL_FILE" --info 2>&1 | head -20
    
    # Check for morph targets more carefully
    echo ""
    echo "🔍 Checking for morph targets..."
    
    node << 'NODESCRIPT'
const fs = require('fs');
const modelPath = process.argv[1];

try {
    const data = fs.readFileSync(modelPath);
    let offset = 12;
    const chunkSize = data.readUInt32LE(offset);
    const chunkType = data.toString('ascii', offset + 4, offset + 8);
    
    if (chunkType === 'JSON') {
        const jsonData = data.toString('utf8', offset + 8, offset + 8 + chunkSize);
        const gltf = JSON.parse(jsonData);
        
        let morphCount = 0;
        if (gltf.meshes) {
            gltf.meshes.forEach(mesh => {
                if (mesh.primitives) {
                    mesh.primitives.forEach(prim => {
                        if (prim.targets) morphCount += prim.targets.length;
                    });
                }
            });
        }
        
        if (morphCount > 0) {
            console.log('✅ SUCCESS: Found ' + morphCount + ' morph targets!');
            console.log('   This model is READY for lip sync animation.');
        } else {
            console.log('❌ WARNING: No morph targets found.');
            console.log('   Choose a different model with blend shapes.');
            process.exit(1);
        }
    }
} catch (err) {
    console.error('Error: ' + err.message);
    process.exit(1);
}
NODESCRIPT
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "STEP 3: Install Model"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        
        # Copy model
        TARGET="$WORKSPACE_DIR/frontend/public/$(basename "$MODEL_FILE")"
        cp "$MODEL_FILE" "$TARGET"
        echo "✅ Copied to: $TARGET"
        
        echo ""
        echo "STEP 4: Update Avatar Configuration"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        
        MODEL_FILENAME=$(basename "$MODEL_FILE")
        echo "Update frontend/src/services/avatar.ts:"
        echo "  Replace: const modelUrl = '/indian_doctor_lipsync.glb'"
        echo "  With:    const modelUrl = '/$MODEL_FILENAME'"
        echo ""
        
        # Ask user to confirm
        read -p "Do you want me to update avatar.ts automatically? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            sed -i "" "s|'/indian_doctor_lipsync.glb'|'/$MODEL_FILENAME'|g" \
                "$WORKSPACE_DIR/frontend/src/services/avatar.ts"
            echo "✅ Updated avatar.ts"
        fi
        
        echo ""
        echo "STEP 5: Test in Browser"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        echo "1. Ensure frontend is running:"
        echo "   cd $WORKSPACE_DIR/frontend"
        echo "   npm run dev"
        echo ""
        echo "2. Open browser: http://localhost:5173"
        echo ""
        echo "3. Test avatar:"
        echo "   - New model should display"
        echo "   - Send a chat message"
        echo "   - Avatar should speak with audio"
        echo "   - If morph targets, mouth will move!"
        echo ""
        echo "4. Check browser console (F12) for errors"
        echo ""
        
        echo "═══════════════════════════════════════════════════════════════"
        echo "✅ INTEGRATION COMPLETE"
        echo "═══════════════════════════════════════════════════════════════"
        echo ""
        echo "Model: $MODEL_FILENAME"
        echo "Location: $TARGET"
        echo ""
        echo "Next steps:"
        echo "  - Refresh browser (Cmd+Shift+R on Mac)"
        echo "  - Test chat and audio playback"
        echo "  - If needed, adjust avatar scale in avatar.ts"
        echo ""
    fi
else
    echo ""
    echo "USAGE:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "  ./quick_model_setup.sh <model.glb>"
    echo ""
    echo "EXAMPLE:"
    echo ""
    echo "  1. Download model from Sketchfab (GLB format)"
    echo "  2. Save to Downloads folder"
    echo "  3. Run:"
    echo "     ./quick_model_setup.sh ~/Downloads/model.glb"
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
fi
