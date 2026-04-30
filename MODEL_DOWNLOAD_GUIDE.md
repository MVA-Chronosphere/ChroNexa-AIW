# Model Selection & Download Guide for ChroNexa Lip Sync

## Problem
Current avatars (pablo_doctor.glb, indian_woman_in_saree.glb) lack facial blend shapes (morph targets) needed for lip sync animation.

## Solution
Download models with built-in facial blend shapes and update the avatar system.

---

## Where to Find Models with Blend Shapes

### 1. **Mixamo** (Recommended)
- **URL**: https://www.mixamo.com
- **Pros**: 
  - Professional quality characters
  - Built-in facial animations and blend shapes
  - Free with Adobe account
  - Reliable export to FBX format
- **Steps**:
  1. Create free Adobe account
  2. Browse "Characters" section
  3. Select character with "Face Shapes" or facial animations
  4. Download as "FBX + Blend Shapes" (important!)
  5. Convert FBX to GLB (see conversion section)

### 2. **Sketchfab** (Free models)
- **URL**: https://sketchfab.com
- **Search filters**: 
  - Set "Downloadable" filter
  - Search: "rigged character" OR "animated character"
  - Check model description for "morph targets" or "blend shapes"
- **Quality examples**:
  - "Scifi Girl v.01" - well-regarded, has animations
  - "Female Character" models with rigged faces
  - Models in "Character" category often include blend shapes
- **Note**: Verify blend shapes exist before downloading

### 3. **Poly Haven**
- **URL**: https://polyhaven.com/models
- **Benefits**: CC0 license, free forever
- **Challenge**: Fewer character models than Mixamo/Sketchfab

### 4. **Free3D / CGTrader Free**
- **Free3D**: https://free3d.com
- **CGTrader Free Models**: https://www.cgtrader.com/free-3d-models?utf8=%E2%9C%93&status=Free
- **Variety**: Large selection, filter by "rigged character"

---

## How to Verify a Model Has Blend Shapes

### Before downloading:
1. Check model preview - look for "animations" or "facial" in description
2. Read comments - users often mention blend shapes
3. Download page - look for these keywords:
   - "Blend shapes"
   - "Morph targets"
   - "Facial animations"
   - "Shapekeys"
   - "Face rig"

### After downloading (GLB inspection):
```bash
# Install GLB inspector
npm install -g gltf-pipeline

# Inspect model
gltf-pipeline -i model.glb --info

# Look for output containing:
# - "morphTargets" count > 0
# - List of target names like: "A", "E", "I", "O", "U", "Smile", etc.
```

---

## Converting Models to GLB Format

### Option 1: Using Blender (Recommended)
1. Install Blender: https://www.blender.org/download/
2. Open model in Blender
3. File → Export → glTF 2.0 (.glb/.gltf)
4. **Important**: Enable these options:
   - ✅ "Include Animations"
   - ✅ "Include Armature"
   - ✅ "Include Blend Shapes" (if available)
   - ✅ "Shape Keys" (important for morph targets)
5. Save as `.glb` format

### Option 2: Using gltf-pipeline (CLI)
```bash
# Install
npm install -g gltf-pipeline

# Convert FBX to GLB
gltf-pipeline -i model.fbx -o model.glb

# Verify blend shapes exist
gltf-pipeline -i model.glb --info | grep -i "morph\|target"
```

### Option 3: Online converters
- https://products.aspose.app/3d/conversion
- https://anyconv.com/
- **Note**: May lose animation data - use Blender for best results

---

## Integration Steps

### 1. Download Model
```bash
# Place downloaded/converted model in public folder
cp ~/Downloads/my_character.glb frontend/public/my_character.glb
```

### 2. Update Avatar Service
Edit `frontend/src/services/avatar.ts`:

```typescript
// Find this line:
const modelUrl = '/pablo_doctor.glb';

// Replace with your model:
const modelUrl = '/my_character.glb';

// Also update this if needed:
const modelUrl2 = '/indian_woman_in_saree.glb'; // or new model
```

### 3. Implement Blend Shape Animation
The lip sync infrastructure is already ready. Once model has blend shapes, add this to avatar.ts `speak()` method:

```typescript
private animateBlendShapes(mouthShapes: string[], timings: number[]) {
  // Called by lip sync engine
  // mouthShapes: ['A', 'E', 'I', 'O', 'U', ...]
  // timings: [start_time, start_time, ...]
  
  if (!this.model) return;
  
  this.model.traverse((node: any) => {
    if (node.morphTargetInfluences) {
      // Apply morph target influences based on mouthShapes
      // See lip_sync_service.py for mouth shape mappings
    }
  });
}
```

### 4. Test in Browser
```bash
# Frontend dev server already running
# Open browser: http://localhost:5173

# Test:
1. Chat interface appears
2. Type message and click Send
3. Avatar should load with new model
4. Audio plays and avatar speaks
5. If model has blend shapes, mouth movement visible
```

---

## Specific Recommended Models

### For Professional Doctor Look:
1. **Mixamo - "Male Doctor"** (if available)
   - Search Mixamo for "doctor" or medical-themed characters
   - Download with blend shapes

2. **Mixamo - Female Professional Characters**
   - "Businesswoman" characters often have facial animations
   - Professional appearance suitable for medical context

3. **Sketchfab - Search**: `scifi woman` + filter downloadable
   - Professional rigged female characters
   - Often include facial animations

### For Indian Heritage Avatar:
1. **Mixamo** - Search for characters with traditional accessories
   - Download and customize with Blender if needed
   
2. **Sketchfab** - Search: `"Indian character"` or `"saree"`
   - User-created Indian characters may have blend shapes
   - Always verify blend shapes before downloading

---

## Troubleshooting

### "Model has no blend shapes"
- ✗ Model incompatible - download different one
- ✓ Solution: Return to "Recommended Models" section, try another

### "Model won't load in avatar"
- Check browser console (F12) for errors
- Verify file path: `/frontend/public/model.glb`
- Test GLB file: gltf-pipeline -i model.glb --info

### "Model loaded but looks wrong (too small/rotated)"
- Edit avatar.ts `loadModel()` method
- Adjust: `model.scale.set(scale, scale, scale)`
- Adjust: `model.position.set(x, y, z)`
- Current settings: `scale=2.8, position=(0, 0.3, 0)`

### "Blend shapes not animating"
- Verify model has blend shapes: gltf-pipeline --info
- Check lip sync service is enabled
- Review browser console for errors

---

## Verification Checklist

Before deploying new model:
- [ ] Model downloaded successfully
- [ ] Model converted to GLB (if needed)
- [ ] GLB file placed in `frontend/public/`
- [ ] Verified blend shapes exist: `gltf-pipeline -i model.glb --info`
- [ ] Updated model URL in `avatar.ts`
- [ ] Browser refreshed (Cmd+Shift+R on Mac)
- [ ] Avatar displays correctly
- [ ] Audio plays and animates
- [ ] Mouth shapes visible (if blend shapes enabled)

---

## Next Steps

1. **Choose a model** from recommended sources above
2. **Download** the model
3. **Convert to GLB** if needed (Blender recommended)
4. **Place in** `frontend/public/`
5. **Update** `avatar.ts` with new model path
6. **Test** in browser at http://localhost:5173
7. **Monitor** browser console for errors
8. **Verify** lip sync works with Rhubarb integration

Once a model with blend shapes is loaded, the existing lip sync infrastructure (Rhubarb CLI + animation system) will automatically work.

---

## Questions?

- Check existing blend shapes: `gltf-pipeline`
- Avatar animation details: `frontend/src/services/avatar.ts`
- Lip sync pipeline: `backend/services/lip_sync_service.py`
- Model requirements: See "Verification Checklist" above
