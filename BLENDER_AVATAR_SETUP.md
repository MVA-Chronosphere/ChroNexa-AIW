# How to Generate Indian Female Doctor Avatar in Blender

## Overview
This guide will walk you through creating a 3D Indian female doctor avatar with lip sync capability using the provided Blender Python script.

**Time Required**: 5-10 minutes
**Result**: GLB file ready for ChroNexa with 10 facial blend shapes for lip sync

---

## Step 1: Open Blender

1. Launch Blender (already installed)
2. You should see the default scene with a cube, camera, and light

---

## Step 2: Open the Script

### Method 1: From File Menu
1. Top Menu: **File > Open Text**
2. Navigate to: `/Users/chiefaiofficer/ChroNexa-AIW/`
3. Select: `create_indian_doctor_avatar.py`
4. Click **"Open Text"**

### Method 2: Copy-Paste
1. Open Text Editor workspace (top of Blender window)
2. New File (⊕ icon)
3. Copy entire `create_indian_doctor_avatar.py` content
4. Paste into editor

---

## Step 3: Run the Script

**Important**: Make sure you're in the **Scripting** workspace at the top of Blender!

### To Run:
1. Click anywhere in the script editor (make sure it's in focus)
2. **Press: Alt + P** (macOS: Shift + Cmd + Return)
3. Or click: **▶ Run Script** button (top right of script editor)

### What Happens:
```
The script will:
1. Delete existing objects
2. Create head (0-5 seconds)
3. Add 10 facial blend shapes (5-15 seconds)
4. Create body parts (15-30 seconds)
5. Add doctor's coat and stethoscope (30-40 seconds)
6. Create skeleton/armature (40-50 seconds)
7. Print success message (50-60 seconds)

Total: 1-2 minutes
```

---

## Step 4: Watch for Success Message

In the **System Console** (bottom of Blender), you should see:

```
✅ INDIAN FEMALE DOCTOR AVATAR CREATED SUCCESSFULLY!

Model Components:
  - Head with 10 facial blend shapes (A, E, I, O, U, F, M, B, P, X)
  - Body (torso, arms, legs)
  - Long black hair
  - White doctor's coat
  - Stethoscope
  - Skeleton armature for animation
```

**If you see this, the script worked! ✓**

---

## Step 5: View the Model

1. Rotate view: **Middle Mouse + Drag** (or trackpad equivalent)
2. Zoom: **Scroll wheel**
3. Pan: **Shift + Middle Mouse + Drag**

You should see:
- ✓ Indian female face
- ✓ Dark long hair
- ✓ White doctor's coat
- ✓ Stethoscope
- ✓ Full body

---

## Step 6: Export as GLB

### Step 6a: Prepare for Export
1. **Select the avatar**: Click on avatar in the viewport
2. Also select armature: Hold **Shift + Click** on "Armature" in outliner (right panel)

### Step 6b: Export Settings
1. **File > Export > glTF 2.0 (.glb/.gltf)**
2. Export Location: `/Users/chiefaiofficer/ChroNexa-AIW/frontend/public/`
3. Filename: `indian_doctor.glb`

### Step 6c: Export Options (IMPORTANT!)
In the export panel on the right, verify:

```
✓ Format: glTF 2.0 (.glb) — select this!
✓ Include:
  ☑ Animation
  ☑ All Armatures
  ☑ All Shapes
  ☑ Export All Objects
  
✓ Data:
  ☑ Armature
  ☑ Deformation Bones
  ☑ Shape Keys
```

### Step 6d: Export
Click: **Export glTF 2.0**

**Success**: File saved to `frontend/public/indian_doctor.glb`

---

## Step 7: Verify Blend Shapes

Open terminal and run:

```bash
cd /Users/chiefaiofficer/ChroNexa-AIW
./verify_model.sh frontend/public/indian_doctor.glb
```

Expected output:
```
✅ FOUND: 10 morph targets
This model is COMPATIBLE with lip sync!
```

If you see this, you're golden! ✓

---

## Step 8: Integrate with ChroNexa

```bash
./quick_model_setup.sh frontend/public/indian_doctor.glb
```

This script will:
1. Verify blend shapes ✓
2. Update avatar.ts to use new model
3. Tell you it's ready

---

## Step 9: Test in Browser

Make sure both backend and frontend are running:

```bash
# Terminal 1: Backend
cd /Users/chiefaiofficer/ChroNexa-AIW/backend
python -m uvicorn app.main:app --reload --port 8000

# Terminal 2: Frontend  
cd /Users/chiefaiofficer/ChroNexa-AIW/frontend
npm run dev
```

Then:

1. **Open browser**: http://localhost:5173
2. **Send a chat message**: "Hello, how are you?"
3. **Watch avatar**:
   - Indian female doctor appears
   - Audio plays
   - Mouth animates with sound (lip sync!)
   - Head bobs with emotion

🎉 **SUCCESS!** Your avatar is working with lip sync!

---

## Troubleshooting

### "Script doesn't run / Error message"
- **Check**: You're in **Scripting** workspace (top menu)
- **Check**: Script file is properly opened
- **Try**: Ctrl+A to select all text, then Run again
- **Try**: Copy entire script again and paste fresh

### "Nothing appears after running"
- **Check**: System Console (View > Toggle System Console)
- **Look for**: Error messages in red
- **Try**: Delete all objects first (Select All > Delete)

### "Export doesn't work"
- **Check**: Location path exists: `frontend/public/`
- **Check**: Filename has `.glb` extension
- **Try**: Choose different location first (Desktop), then move file

### "Blend shapes not working in ChroNexa"
- **Verify**: `./verify_model.sh` shows "10 morph targets"
- **Check**: Browser console (F12) for errors
- **Try**: Refresh page (Cmd+Shift+R on Mac)

### "Model looks weird/deformed"
- **Normal**: First generation might have minor geometry issues
- **Solution**: Smooth shading is applied, should look good
- **Try**: Rotate view to see from different angle

---

## If Export Fails

**Alternative Export Path:**

If standard export doesn't work:

1. **File > Export > Wavefront (.obj)**
   - Save as: `indian_doctor.obj`
   
2. **Re-import and convert**:
   - New Blender window
   - File > Import > Wavefront (.obj)
   - Select: `indian_doctor.obj`
   - File > Export > glTF 2.0 (.glb)

3. **Or use online converter**:
   - https://products.aspose.app/3d/conversion
   - Upload: `indian_doctor.obj`
   - Download: `indian_doctor.glb`

---

## Next Steps After Export

```bash
# 1. Verify blend shapes (10 morph targets)
./verify_model.sh frontend/public/indian_doctor.glb

# 2. Integrate with ChroNexa
./quick_model_setup.sh frontend/public/indian_doctor.glb

# 3. Test in browser
open http://localhost:5173

# 4. Send chat message and watch avatar
```

---

## Model Customization (Optional)

Want to modify the avatar before exporting?

### Change Hair Color
- In Blender, select "Hair" object
- In Properties (right panel) > Material Properties
- Click "Hair" material
- Change Base Color to desired shade

### Change Skin Tone
- Select head or body parts
- Change "Skin" material color
- Options: Lighter/darker Indian tones

### Adjust Size
- Select avatar in outliner
- Properties > Scale
- Multiply by 1.2 for larger, 0.8 for smaller

### Change Clothing
- Edit "Coat" material color (white to blue for nursing scrubs)
- Modify coat geometry (advanced)

---

## Important Notes

✅ **This avatar works with ChroNexa because:**
- Has 10 facial blend shapes (A, E, I, O, U, F, M, B, P, X)
- Proper GLB export format
- Includes skeleton for future body animations
- Realistic materials and colors

⚠️ **Lip sync requires:**
- Model with blend shapes ✓ (this avatar has them)
- Rhubarb CLI ✓ (already installed)
- Backend integration ✓ (already done)
- Frontend avatar service ✓ (already done)

✨ **Everything is ready to work together!**

---

## Questions?

If something doesn't work:

1. Check **System Console** for error messages
2. Verify file locations
3. Try running the script again (clean start)
4. Check model with: `./verify_model.sh`

Good luck! Your Indian female doctor avatar with lip sync is coming to life! 🎉
