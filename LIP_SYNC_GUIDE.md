# Lip Sync Implementation Guide

## Overview

This guide explains ChroNexa's lip sync implementation and how to enable true mouth animation synchronized with audio.

## Current Status

### ✅ Completed Infrastructure
- **Rhubarb CLI**: Installed v1.14.0 at `/Users/chiefaiofficer/.local/bin/rhubarb`
- **Backend lip sync service**: Fully implemented (`backend/services/lip_sync_service.py`)
- **TTS audio generation**: Working with Rhubarb analysis
- **Three.js avatar framework**: Ready for blend shape animation
- **Audio playback**: Browser Web Audio API with frequency analysis
- **Audio-reactive animation**: Head bob and body scale (fallback)

### ⏳ In Progress
- **Model replacement**: Need models with blend shapes (morph targets)
- **Blend shape animation**: Ready to implement once models updated

### 🔴 Blocked By
- **Current model limitation**: Both `pablo_doctor.glb` and `indian_woman_in_saree.glb` **lack facial blend shapes**
- **Solution**: Replace with models that have morph targets

---

## The Problem: Current Models

**Analysis Result:**
```
pablo_doctor.glb:     ❌ NO morph targets detected
indian_woman_in_saree.glb: ❌ NO morph targets detected
```

**Without blend shapes:**
- ✗ Cannot animate mouth shapes
- ✗ Rhubarb data cannot be visualized
- ✓ Audio-reactive fallback works (head bob)

**Solution:** Download/create models with facial blend shapes.

---

## Three Solutions

### **Option A: Download Ready-Made Models** ⭐ RECOMMENDED
- **Time**: 5 minutes
- **Difficulty**: Very easy
- **Best for**: Immediate deployment
- **How**: Download GLB from Sketchfab, verify blend shapes, replace
- **Resource**: [RECOMMENDED_MODELS.md](./RECOMMENDED_MODELS.md)

### **Option B: Use Mixamo + Blender**
- **Time**: 20-30 minutes
- **Difficulty**: Medium
- **Best for**: Professional quality, customization
- **How**: Download character → convert FBX to GLB → replace
- **Resource**: [MODEL_DOWNLOAD_GUIDE.md](./MODEL_DOWNLOAD_GUIDE.md)

### **Option C: Audio-Reactive Animation** (Current Workaround)
- **Time**: Already implemented
- **Difficulty**: N/A (deployed)
- **Status**: ⚠️ Insufficient for full lip sync
- **Limitation**: Head bob/body scale, not mouth movement
- **When**: Use as fallback only

---

## Solution Comparison

| Aspect | Option A | Option B | Option C |
|--------|----------|----------|----------|
| Time to implement | 5 min | 30 min | N/A (done) |
| Difficulty | Very easy | Medium | N/A |
| Quality | Good | Excellent | Poor |
| Customization | No | Yes | No |
| True lip sync | ✅ Yes | ✅ Yes | ❌ No |
| Requires tools | No | Blender | No |
| Ready now | ✅ Yes | ⏳ Soon | ✅ Yes |

---

## Quick Start - Option A (5 minutes)

### 1. Download Model with Blend Shapes
```bash
# Go to: https://sketchfab.com/search?type=models&downloadable=true
# Search: "female character" or "rigged character"
# Download: GLB format (NOT FBX)
# Save to: ~/Downloads/model.glb

# Verify it has blend shapes:
cd /Users/chiefaiofficer/ChroNexa-AIW
./verify_model.sh ~/Downloads/model.glb

# Expected output:
# ✅ FOUND: X morph targets
# This model is COMPATIBLE with lip sync!
```

### 2. Integrate with ChroNexa
```bash
./quick_model_setup.sh ~/Downloads/model.glb

# This script will:
# - Verify blend shapes exist
# - Copy model to frontend/public/
# - Update avatar.ts to use new model
# - Show next steps
```

### 3. Test in Browser
```bash
# Ensure both running:
# Terminal 1: cd backend && python -m uvicorn app.main:app --reload
# Terminal 2: cd frontend && npm run dev

# Browser: http://localhost:5173
# 1. Send chat message
# 2. Watch avatar speak
# 3. Mouth should animate!
```

---

## Manual Setup - Option A (If scripts don't work)

### Step 1: Replace Model File
```bash
# Copy downloaded GLB to public folder
cp ~/Downloads/model.glb /Users/chiefaiofficer/ChroNexa-AIW/frontend/public/new_avatar.glb
```

### Step 2: Update Avatar Service
Edit `frontend/src/services/avatar.ts`:
```typescript
// Find this line (around line 50):
const modelUrl = '/pablo_doctor.glb';

// Replace with:
const modelUrl = '/new_avatar.glb';
```

### Step 3: Verify and Test
```bash
# Refresh browser
# Open http://localhost:5173
# Send a message
# Avatar should display with new model and animate mouth
```

---

## What's Needed for Lip Sync

### 1. Model with Blend Shapes ✅ Solution Available
- **What**: 3D model must have morph targets (blend shapes)
- **Common shapes**: A, E, I, O, U, F, M, B, P, X (silence)
- **Check**: `./verify_model.sh model.glb`
- **Where to find**: RECOMMENDED_MODELS.md

### 2. Rhubarb CLI ✅ Already Installed
- **Status**: Installed v1.14.0
- **Location**: `/Users/chiefaiofficer/.local/bin/rhubarb`
- **Function**: Analyzes audio → generates mouth shape sequence
- **Verify**: `rhubarb --version`

### 3. Backend Integration ✅ Already Implemented
- **Service**: `backend/services/lip_sync_service.py`
- **Endpoint**: POST `/api/avatar/tts`
- **Output**: Includes `lip_sync` field with mouth shapes and timing
- **Status**: Ready to use with any model that has blend shapes

### 4. Frontend Animation ✅ Framework Ready
- **Service**: `frontend/src/services/avatar.ts`
- **Framework**: Three.js morphTargetInfluences system
- **Status**: Ready to connect Rhubarb output to animation

---

## How It Works (Architecture)

```
User types message
        ↓
ChatInterface sends to /api/avatar/tts
        ↓
Backend TTS Service generates audio + saves to temp file
        ↓
Rhubarb CLI analyzes audio file
        ↓
Rhubarb outputs JSON: {"mouthCues": [{"start": 0.1, "value": "A"}, ...]}
        ↓
Backend parses Rhubarb output
        ↓
Backend returns:
  {
    "audio_url": "data:audio/wav;base64,...",
    "duration": 2.5,
    "lip_sync": {
      "mouth_shapes": ["X", "A", "E", "I", "O", "U", ...],
      "timings": [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, ...]
    }
  }
        ↓
Frontend receives response
        ↓
Frontend plays audio + animates avatar's blend shapes
        ↓
Avatar's mouth moves in sync with audio! 🎉
```

---

## Rhubarb Output Format

Example output when audio is analyzed:
```json
{
  "metadata": {
    "soundFile": "audio.wav",
    "duration": 2.5
  },
  "mouthCues": [
    {"start": 0.0, "value": "X"},  // Closed mouth
    {"start": 0.1, "value": "A"},  // Open (ah)
    {"start": 0.2, "value": "E"},  // Smile (eh)
    {"start": 0.3, "value": "I"},  // Narrow (ee)
    {"start": 0.4, "value": "O"},  // Round (oh)
    {"start": 0.5, "value": "U"},  // Pursed (oo)
    {"start": 0.6, "value": "X"}   // Close
  ]
}
```

**Mouth shapes legend:**
- **X**: Silence / closed mouth
- **A**: Wide open (ah)
- **E**: Smile/grin (eh)
- **I**: Narrow (ee)
- **O**: Round (oh)
- **U**: Pursed (oo)
- **F**: Teeth visible
- **M**: Closed lips (mm)
- **B**: Bilabial (bb/pp)
- **P**: Other

---

## Troubleshooting

### "Model has no blend shapes"
```bash
# Check with:
./verify_model.sh model.glb

# If output shows ❌ NOT FOUND:
# - Model is incompatible
# - Choose different model from RECOMMENDED_MODELS.md
# - Try Sketchfab search: "blend shapes" or "facial animation"
```

### "Rhubarb not found"
```bash
# Verify installation:
which rhubarb
# Should output: /Users/chiefaiofficer/.local/bin/rhubarb

rhubarb --version
# Should show: Rhubarb v1.14.0 or similar

# Check settings:
cat backend/config/settings.py | grep rhubarb_path
```

### "Avatar won't update after replacing model"
```bash
# 1. Hard refresh browser: Cmd+Shift+R (Mac)
# 2. Check file path in avatar.ts
# 3. Verify file exists: frontend/public/model.glb
# 4. Check browser console (F12) for errors
```

### "Mouth not animating"
```bash
# 1. Verify model has blend shapes:
./verify_model.sh frontend/public/model.glb

# 2. Check backend is working:
curl -X POST http://localhost:8000/api/avatar/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "Test"}' | grep "lip_sync"

# 3. Check browser console for JavaScript errors
```

### "Audio and mouth out of sync"
- Timing adjustment in avatar.ts
- Check browser network latency
- Verify Rhubarb output has correct timing

---

## Implementation Steps for Blend Shape Animation

Once you have a model with blend shapes:

### Step 1: Verify Model
```bash
./verify_model.sh model.glb
# Should show: ✅ FOUND: X morph targets
```

### Step 2: Add to Frontend
```bash
cp model.glb frontend/public/
```

### Step 3: Update Avatar Service
Edit `frontend/src/services/avatar.ts` and add blend shape animation:

```typescript
// Add this method to IndianDoctorAvatar class:
private applyBlendShape(shapeIndex: number, intensity: number) {
  if (!this.model) return;
  
  this.model.traverse((node: any) => {
    if (node.morphTargetInfluences && 
        shapeIndex < node.morphTargetInfluences.length) {
      // Reset all shapes
      node.morphTargetInfluences.forEach((_, i) => {
        node.morphTargetInfluences[i] = i === shapeIndex ? intensity : 0;
      });
    }
  });
}

// Update speak() method to use lip sync data:
public speak(duration: number, audioElement?: HTMLAudioElement) {
  // ... existing code ...
  
  // NEW: Apply lip sync if available
  const lipSyncData = this.lastLipSyncData; // Store from API response
  if (lipSyncData) {
    this.applyLipSyncAnimation(lipSyncData);
  }
}

private applyLipSyncAnimation(lipSyncData: any) {
  const mouthShapeMap: Record<string, number> = {
    'A': 0, 'E': 1, 'I': 2, 'O': 3, 'U': 4,
    'F': 5, 'M': 6, 'B': 7, 'P': 8, 'X': 9
  };
  
  lipSyncData.mouth_shapes.forEach((shape: string, idx: number) => {
    const shapeIdx = mouthShapeMap[shape] ?? 9;
    const timing = (lipSyncData.timings[idx] ?? 0) * 1000; // Convert to ms
    
    setTimeout(() => {
      this.applyBlendShape(shapeIdx, 1.0);
    }, timing);
  });
}
```

### Step 4: Connect Frontend to Backend
Edit `frontend/src/components/ChatInterface.tsx`:
```typescript
const response = await api.generateAndPlayAudio(text);

// NEW: Store lip sync data for animation
if (response.lip_sync) {
  avatarService.setLipSyncData(response.lip_sync);
}
```

### Step 5: Test
```bash
# Send chat message
# Audio plays + avatar mouth animates
```

---

## Resources

- **Rhubarb GitHub**: https://github.com/DanielSWolf/rhubarb-lip-sync
- **Model Download**: [RECOMMENDED_MODELS.md](./RECOMMENDED_MODELS.md)
- **Model Guide**: [MODEL_DOWNLOAD_GUIDE.md](./MODEL_DOWNLOAD_GUIDE.md)
- **Three.js Blend Shapes**: https://threejs.org/docs/#api/en/core/BufferGeometry.morphAttributes
- **Blender Shape Keys**: https://docs.blender.org/manual/en/latest/animation/shape_keys/introduction.html

---

## Next Steps - Start Here

### Fastest Path (5 minutes):
1. Download model from Sketchfab
2. Run: `./quick_model_setup.sh model.glb`
3. Refresh browser
4. Test ✅

### See Details:
- Model selection: [RECOMMENDED_MODELS.md](./RECOMMENDED_MODELS.md)
- Conversion/setup: [MODEL_DOWNLOAD_GUIDE.md](./MODEL_DOWNLOAD_GUIDE.md)
- Code implementation: See "Implementation Steps" section above

---

## Status Summary

| Component | Status | Notes |
|-----------|--------|-------|
| Rhubarb CLI | ✅ Installed | v1.14.0, tested |
| Lip sync service | ✅ Ready | Backend fully implemented |
| TTS generation | ✅ Working | Pyttsx3 + fallback |
| Audio playback | ✅ Ready | Web Audio API |
| Model with blend shapes | ⏳ Action required | Choose from RECOMMENDED_MODELS.md |
| Blend shape animation | ✅ Code ready | Framework ready, needs model |
| Audio-reactive fallback | ✅ Active | Working now, will be replaced |

**Bottleneck:** Replace models with ones containing facial blend shapes.

**Action:** Follow Option A or B above to download/integrate a compatible model.
