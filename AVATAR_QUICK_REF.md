# Quick Reference: Avatar Generation

## Files
- **Script**: `/Users/chiefaiofficer/ChroNexa-AIW/create_indian_doctor_avatar.py`
- **Instructions**: `BLENDER_AVATAR_SETUP.md` (same folder)

---

## 5-Minute Quick Start

### 1. Open Blender
   - Launch Blender app

### 2. Load Script
   - **File > Open Text**
   - Select: `create_indian_doctor_avatar.py`
   - Click **Open Text**

### 3. Run Script
   - Make sure in **Scripting** workspace
   - Press: **Alt + P** (Mac: Shift + Cmd + Return)
   - Wait 1-2 minutes for generation

### 4. Check Success
   - Look at System Console (bottom)
   - Should show: ✅ INDIAN FEMALE DOCTOR AVATAR CREATED!

### 5. Export as GLB
   - Select avatar + armature
   - **File > Export > glTF 2.0 (.glb)**
   - Location: `frontend/public/`
   - Filename: `indian_doctor.glb`
   - Export!

### 6. Verify
   ```bash
   cd /Users/chiefaiofficer/ChroNexa-AIW
   ./verify_model.sh frontend/public/indian_doctor.glb
   ```
   Should show: ✅ FOUND: 10 morph targets

### 7. Integrate
   ```bash
   ./quick_model_setup.sh frontend/public/indian_doctor.glb
   ```

### 8. Test
   - Open: http://localhost:5173
   - Send a message
   - Watch avatar speak with lip sync!

---

## Avatar Features

✓ Indian female doctor appearance
✓ Dark long hair
✓ White doctor's coat
✓ Stethoscope
✓ 10 facial blend shapes (A, E, I, O, U, F, M, B, P, X)
✓ Skeleton for animation
✓ Realistic materials

---

## Export Settings (Must Check!)

Before clicking Export:
- ✓ Format: glTF 2.0 (.glb)
- ✓ Include: Animation
- ✓ Include: All Armatures  
- ✓ Include: All Shapes
- ✓ Include: All Objects

---

## If Problems

**Script won't run:**
- Check in Scripting workspace
- Try: Ctrl+A (select all), then Run

**Export fails:**
- Verify path: frontend/public/ exists
- Try different filename
- Use online converter if needed

**Blend shapes not found:**
- Run: `./verify_model.sh` to check
- If 0 morph targets, re-export from Blender with Shape Keys enabled

---

## Verification Commands

```bash
# Check blend shapes exist
./verify_model.sh frontend/public/indian_doctor.glb

# Setup integration
./quick_model_setup.sh frontend/public/indian_doctor.glb

# Test backend
curl -X POST http://localhost:8000/api/avatar/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello"}'
```

---

## File Locations

| Item | Path |
|------|------|
| Script | `/Users/chiefaiofficer/ChroNexa-AIW/create_indian_doctor_avatar.py` |
| Instructions | `BLENDER_AVATAR_SETUP.md` |
| Output GLB | `/Users/chiefaiofficer/ChroNexa-AIW/frontend/public/indian_doctor.glb` |
| Frontend | `http://localhost:5173` |
| Backend | `http://localhost:8000` |

---

## Timeline

| Step | Time |
|------|------|
| Open Blender | 30 sec |
| Load + Run Script | 1-2 min |
| Export as GLB | 30 sec |
| Verify blend shapes | 10 sec |
| Integrate with ChroNexa | 10 sec |
| Test in browser | 30 sec |
| **Total** | **~5 minutes** |

---

## Success Indicators

✓ Avatar visible in Blender viewport
✓ System Console shows "✅ CREATED SUCCESSFULLY!"
✓ GLB file saved to `frontend/public/indian_doctor.glb`
✓ Verify script shows: "✅ FOUND: 10 morph targets"
✓ Browser shows Indian female doctor avatar
✓ Mouth animates when avatar speaks

---

## Next After Success

1. ✓ Avatar model created
2. ✓ Blend shapes working
3. ✓ Integrated with ChroNexa
4. ✓ Lip sync ready
5. → Test chat functionality
6. → Fine-tune appearance (optional)
7. → Deploy to production

---

## Full Instructions

See: `BLENDER_AVATAR_SETUP.md` in same folder

Questions? Check troubleshooting section in full guide!
