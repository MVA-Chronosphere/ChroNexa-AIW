#!/bin/bash
# Debug script to check avatar model and loading issues

echo "================================"
echo "ChroNexa Avatar Debug"
echo "================================"
echo ""

# Check file exists
echo "1. Checking model file..."
if [ -f "frontend/public/indian_doctor_lipsync.glb" ]; then
    SIZE=$(ls -lh frontend/public/indian_doctor_lipsync.glb | awk '{print $5}')
    echo "   ✓ Model file exists: $SIZE"
else
    echo "   ✗ Model file NOT found!"
    exit 1
fi

# Check backend
echo ""
echo "2. Checking backend..."
curl -s -o /dev/null -w "   %{http_code} " http://localhost:8000/api/avatar/tts || echo "ERROR"
echo ""

# Check frontend
echo ""
echo "3. Checking frontend..."
curl -s -o /dev/null -w "   %{http_code} " http://localhost:3000 || echo "ERROR"
echo ""

# Verify blend shapes
echo ""
echo "4. Verifying blend shapes..."
python3 << 'EOF'
import json
import struct

try:
    with open("frontend/public/indian_doctor_lipsync.glb", "rb") as f:
        data = f.read()
        offset = 12
        chunk_size = struct.unpack('<I', data[offset:offset+4])[0]
        chunk_type = data[offset+4:offset+8].decode('ascii')
        
        if chunk_type == 'JSON':
            json_data = data[offset+8:offset+8+chunk_size].decode('utf-8')
            gltf = json.loads(json_data)
            
            morph_count = 0
            if 'meshes' in gltf:
                for mesh in gltf['meshes']:
                    if 'primitives' in mesh:
                        for prim in mesh['primitives']:
                            if 'targets' in prim:
                                morph_count += len(prim['targets'])
            
            print(f"   Morph targets: {morph_count}")
            print(f"   Meshes: {len(gltf.get('meshes', []))}")
            print(f"   Nodes: {len(gltf.get('nodes', []))}")
except Exception as e:
    print(f"   Error: {e}")
EOF

echo ""
echo "5. Browser console hints:"
echo "   - Open browser DevTools: F12"
echo "   - Check Console tab for errors"
echo "   - Look for '[IndianDoctorAvatar]' messages"
echo "   - Check Network tab for failed GLB request"
echo ""
echo "6. Try these if avatar still missing:"
echo "   - Hard refresh: Cmd+Shift+R (Mac)"
echo "   - Check CORS headers"
echo "   - Verify frontend/src/services/avatar.ts loaded properly"
echo "   - Check if model too small: resize output canvas"
echo ""
echo "Done!"
