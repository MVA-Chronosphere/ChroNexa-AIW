# Recommended 3D Models with Blend Shapes for ChroNexa

This document provides specific, tested models that work with ChroNexa's lip sync system.

## Quick Start

**Best option for immediate testing:**

1. **Download** one of the Sketchfab models below
2. **Run** `./quick_model_setup.sh /path/to/model.glb`
3. **Refresh** browser to see new avatar
4. **Test** chat functionality

---

## Tier 1: Ready-to-Use Models (Verified with Blend Shapes)

### 1.1 Scifi Girl v.01 (Sketchfab)
- **Status**: ✅ Verified - Has morph targets
- **URL**: https://sketchfab.com/3d-models/scifi-girl-v01-96340701c2ed4d37851c7d9109eee9c0
- **Download Format**: GLB (directly compatible)
- **Quality**: Excellent - Professional rigged female character
- **Blend Shapes**: ✅ Multiple facial animations
- **License**: Check on page before download
- **Steps**:
  ```bash
  # 1. Visit URL above and click "Download"
  # 2. Place in Downloads folder
  # 3. Run:
  ./quick_model_setup.sh ~/Downloads/scifi_girl.glb
  ```

### 1.2 Female Character Rigged (Sketchfab)
- **Status**: ✅ Likely has blend shapes (verify first)
- **URL**: https://sketchfab.com/search?q=female+character&type=models&downloadable=true&sort_by=-likeCount
- **Download Format**: GLB preferred
- **How to Select**:
  1. Browse top results (sorted by likes)
  2. Click each model
  3. Check description for: "blend shapes", "morph targets", "facial animations"
  4. Look for "Rigged" badge
  5. Download GLB format
- **Verification**:
  ```bash
  ./verify_model.sh ~/Downloads/model.glb
  ```

---

## Tier 2: Mixamo Models (Requires Free Adobe Account)

### 2.1 Why Mixamo?
- ✅ Professional quality characters
- ✅ Guaranteed facial blend shapes when downloaded correctly
- ✅ Extensive animation library
- ✅ Consistent rigging across all characters
- ❌ Requires Adobe account (free)
- ❌ Need conversion FBX → GLB

### 2.2 How to Download Mixamo Model with Blend Shapes

**Step 1: Create/Login to Adobe Account**
- Visit: https://www.mixamo.com
- Click "Sign in with Adobe"
- Create free account if needed

**Step 2: Select Character**
- Browse "Characters" category
- Look for professional/doctor-like characters:
  - "Female Doctor" (if available)
  - "Businesswoman"
  - "Business Person"
  - "Professional Male/Female"
- Click character to view details

**Step 3: Download with Blend Shapes**
- Click "Download"
- Select format: **FBX**
- Enable: **✅ Blend Shapes** (critical!)
- Enable: **✅ Skin**
- Enable: **✅ Bones**
- Click "Download"

**Step 4: Convert FBX to GLB**
```bash
# Install Blender (one-time)
# Download from: https://www.blender.org/download/

# Option A: Use Blender GUI (easier)
# 1. Open Blender
# 2. File > Open > Select .fbx
# 3. File > Export > glTF 2.0 (.glb)
# 4. Enable:
#    - Include Animations
#    - Include Blend Shapes
#    - Export All Shape Keys
# 5. Save

# Option B: Use gltf-pipeline (CLI)
npm install -g gltf-pipeline
gltf-pipeline -i model.fbx -o model.glb

# Verify result
./verify_model.sh model.glb
```

**Step 5: Integrate with ChroNexa**
```bash
./quick_model_setup.sh model.glb
```

### 2.3 Recommended Mixamo Characters
- "Female 1" - Professional appearance
- "Female 3" - Diverse character options
- "Business Person" - Corporate-friendly look
- Any character with facial animations listed

---

## Tier 3: Other Sources

### 3.1 Free3D Models
- **URL**: https://free3d.com
- **Search**: "Rigged Character" + "Blend Shapes"
- **Download**: Usually FBX, requires conversion
- **Process**: FBX → Blender → GLB conversion
- **Note**: Quality varies, verify before use

### 3.2 CGTrader Free Models
- **URL**: https://www.cgtrader.com/free-3d-models
- **Filter**: "Characters", "Rigged"
- **Download**: Various formats
- **Quality**: Professional-grade
- **Process**: May require format conversion

### 3.3 Poly Haven
- **URL**: https://polyhaven.com/models
- **License**: CC0 (free to use)
- **Selection**: Limited character models
- **Advantage**: No license restrictions
- **Search**: "character" in model search

---

## Model Selection Checklist

Before downloading a model, verify it has:

- ✅ **Facial animations** or "blend shapes" mentioned
- ✅ **Rigged skeleton** (for body animation)
- ✅ **Professional appearance** (suitable for doctor/medical context)
- ✅ **Downloadable** in GLB or FBX format
- ✅ **License allows** web/commercial use
- ✅ **Not obvious AI-generated** artifacts (optional)

---

## Conversion Reference

### When You Need Conversion (FBX → GLB)

**Situation**: Downloaded FBX from Mixamo or other source

**Solution 1: Blender (Recommended)**
```bash
# Install Blender: https://www.blender.org/download/
# Then in Blender:
# File > Open > model.fbx
# File > Export > glTF 2.0 (.glb)
# ENABLE THESE OPTIONS:
#   ✅ Include Animations
#   ✅ Include Armature
#   ✅ Include Shape Keys
#   ✅ Bake Animation
# Export
```

**Solution 2: Online Converter**
- https://products.aspose.app/3d/conversion (FBX → GLTF)
- Upload FBX, download GLTF
- May lose some animation data
- Use Blender for best results

**Solution 3: Three.js Editor**
- https://threejs.org/editor/
- Import FBX
- Export as glTF
- May require tweaking

---

## Testing Your Model

### Quick Test with Verification Script
```bash
./verify_model.sh frontend/public/model.glb
```

Expected output if successful:
```
✓ Valid GLB format
GEOMETRY INFORMATION:
  Meshes: N
  Nodes: N
  Animations: N
BLEND SHAPES (MORPH TARGETS):
  ✅ FOUND: X morph targets
  This model is COMPATIBLE with lip sync!
```

### Full Integration Test
```bash
# Assuming model is already in frontend/public/

# 1. Ensure backend is running
cd backend
python -m uvicorn app.main:app --reload --port 8000

# 2. Ensure frontend is running (in another terminal)
cd frontend
npm run dev

# 3. Open browser
open http://localhost:5173

# 4. Test:
#   - Avatar should display with new model
#   - Type message in chat
#   - Audio should play
#   - Avatar should speak
#   - If model has blend shapes, mouth will animate
```

---

## Troubleshooting Downloads

### "Download button not working"
- Check browser console for errors
- Try different browser (Chrome, Firefox)
- Check if authenticated (for Mixamo)

### "Downloaded file is huge (>100MB)"
- May include textures/materials
- Compress with gltf-pipeline:
  ```bash
  gltf-pipeline -i large.glb -o small.glb --draco
  ```

### "File won't convert/open in Blender"
- Try online converter first
- If conversion fails, choose different model
- Some old FBX formats incompatible

### "Model too small/large in ChroNexa"
- Model will display but may need scaling
- Edit `frontend/src/services/avatar.ts`:
  ```typescript
  // Find line: model.scale.set(2.8, 2.8, 2.8)
  // Adjust number to scale (higher = bigger)
  model.scale.set(3.5, 3.5, 3.5);  // Larger
  model.scale.set(2.0, 2.0, 2.0);  // Smaller
  ```

---

## Recommended Path Forward

### Fastest Path (5 minutes)
1. Download Scifi Girl v.01 from Sketchfab URL above
2. Run: `./quick_model_setup.sh ~/Downloads/scifi_girl.glb`
3. Refresh browser
4. Test chat

### Professional Path (20 minutes)
1. Create Adobe account
2. Download character from Mixamo with blend shapes
3. Convert FBX to GLB in Blender
4. Run: `./quick_model_setup.sh model.glb`
5. Adjust scale if needed
6. Test chat

### Custom Path
1. Search for specific theme (doctor, Indian heritage, etc.)
2. Verify blend shapes exist
3. Convert if needed
4. Integrate with ChroNexa
5. Customize appearance in Blender if desired

---

## FAQ

**Q: Do I need Blender?**
A: Only if downloading FBX format. Sketchfab GLB models are ready to use.

**Q: How long does conversion take?**
A: Usually < 5 minutes in Blender, even faster with gltf-pipeline CLI.

**Q: Will lip sync work immediately?**
A: Yes, if model has blend shapes. Infrastructure is ready.

**Q: Can I customize the model?**
A: Yes, use Blender to edit appearance before conversion.

**Q: What if model looks wrong (rotated/small)?**
A: Edit `avatar.ts` scale/position settings (takes 30 seconds).

**Q: Can I use multiple models?**
A: Yes, update `avatar.ts` to load different models.

---

## Next Steps

1. **Choose a model** from Tier 1 (fastest) or Tier 2 (professional)
2. **Download** using provided links/instructions
3. **Verify** with: `./verify_model.sh model.glb`
4. **Integrate** with: `./quick_model_setup.sh model.glb`
5. **Test** at http://localhost:5173
6. **Monitor console** for any errors (F12)

---

**Ready to try it?** Download a Sketchfab model and run `./quick_model_setup.sh` now!
