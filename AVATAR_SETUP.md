# Setting Up a Realistic Doctor Avatar

## Quick Start: Using a Pre-made Model

### Option 1: Ready Player Me (Recommended) ✅
1. Go to https://readyplayer.me/
2. Create a free account and customize your avatar as a doctor
3. Download the `.glb` file
4. Save it to: `/Users/chiefaiofficer/ChroNexa-AIW/frontend/public/avatar.glb`
5. The app will automatically load it!

### Option 2: Sketchfab Model
1. Visit https://sketchfab.com/search?q=doctor+avatar
2. Find a model marked as "Downloadable"
3. Download the `.glb` file
4. Save to: `/Users/chiefaiofficer/ChroNexa-AIW/frontend/public/avatar.glb`

### Option 3: Use Your Own Hosted Model
1. Host your `.glb` file online (GitHub, Vercel, AWS S3, etc.)
2. Update `frontend/src/services/avatar.ts` line 82-87:
```typescript
const modelUrls = [
  'https://your-hosted-url.com/doctor-avatar.glb',
  '/avatar.glb'  // fallback to local
]
```

## Testing Your Avatar

After placing or uploading a model:

1. **Hard refresh** your browser: `Cmd+Shift+R`
2. Open DevTools Console (F12)
3. Look for messages like:
   - `[IndianDoctorAvatar] Trying to load model from...`
   - `[IndianDoctorAvatar] Model loaded successfully`
4. Your avatar should appear in the left panel

## If Model Doesn't Load

Check the Console for error messages. The app will automatically fall back to a simple procedural avatar if loading fails.

## Recommended Free Avatar Resources

- **Ready Player Me**: https://readyplayer.me (Easiest, customizable)
- **Sketchfab Free**: https://sketchfab.com (Search "doctor" or "medical")
- **Quaternius**: https://quaternius.com (Simple, stylized)
- **CGTrader Free**: https://www.cgtrader.com/free-3d-models (Search "doctor")

## Model Requirements

- Format: `.glb` or `.gltf`
- Size: Keep under 50MB for faster loading
- Proportions: Should look good at scale (1.5x, 1.5x, 1.5x)
- Optional: Animations for idle/talking states

## Next Steps

1. Get your avatar model file
2. Place it in `/frontend/public/avatar.glb` OR upload online
3. Update the URL if using hosted version
4. Refresh browser to see your realistic doctor avatar!

---

Once your avatar is set up, you can proceed with:
- Text-to-speech integration
- Lip-sync animations
- Chat functionality testing
