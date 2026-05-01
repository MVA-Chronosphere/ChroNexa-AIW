# Generate Custom Indianized Doctor Avatar - Free Tools Guide

## Step 1: Generate the Avatar Image (FREE)

Choose one of these free AI image generators:

### Option A: Leonardo.AI (RECOMMENDED - Free)
1. Go to https://leonardo.ai/ (free tier available)
2. Sign up with Google/GitHub
3. Use **Image Generation** → Text-to-Image
4. **Prompt to use:**
```
A professional female Indian person, 
Indian facial features, brown skin tone,
warm welcoming expression,
realistic portrait, front view,
neutral background,
high quality, detailed face,
character design avatar
```
5. **Settings:**
   - Model: Leonardo Vision XL
   - Guidance Scale: 7-8
   - Number of Images: 4 (to choose the best)
6. Download the best image (PNG format)

### Option B: Stable Diffusion (Ultra Free - Local)
1. Install: https://github.com/AUTOMATIC1111/stable-diffusion-webui
2. Run locally on your machine
3. Use same prompt as above

### Option C: BlueWillow (Free)
1. Go to https://www.bluewillow.ai/
2. Discord bot - free tier available
3. Use same prompt

---

## Step 2: Convert Image to 3D Model (FREE)

### Option A: Meshy.AI (RECOMMENDED)
1. Go to https://www.meshy.ai/
2. Sign up (free tier: 20 monthly credits)
3. Click **"Text to 3D"** or **"Image to 3D"**
4. Upload your generated image
5. **Settings:**
   - Style: Realistic
   - Quality: Medium (free tier)
6. Wait ~2-5 minutes for processing
7. Download as **.GLB** file

### Option B: Kaedim (Free Tier)
1. Go to https://www.kaedim3d.com/
2. Sign up with email
3. Upload your image
4. Select "Auto Refine"
5. Download as **.GLB**

### Option C: Spline (Free, Web-based)
1. Go to https://spline.design/
2. Upload your image
3. Use AI tools to convert
4. Export as GLB

---

## Step 3: Add to ChroNexa Project

1. Download the `.glb` file from the 3D generator
2. Rename it to: `avatar_indian_doctor.glb`
3. Move to: `/Users/chiefaiofficer/ChroNexa-AIW/frontend/public/`
4. Update the model reference in code:

```bash
# Option A: Replace the config to use your new model
# Edit: frontend/src/services/avatar.ts
# Change line: const modelUrl = '/avatar_indian_doctor.glb'
```

5. Hard refresh browser: **Cmd + Shift + R**

---

## Quick Summary

| Step | Tool | Time | Cost |
|------|------|------|------|
| 1. Generate Image | Leonardo.AI | 2-5 min | FREE |
| 2. Convert to 3D | Meshy.AI | 2-5 min | FREE |
| 3. Add to Project | Manual | 1 min | FREE |
| **Total Time** | | **5-10 min** | **$0** |

---

## Troubleshooting

**Model too large?**
- Use Meshy.AI "Medium" quality
- Most GLB files are 2-10 MB (acceptable)

**Model looks weird?**
- Try different prompts (add "professional", "friendly", "welcoming")
- Generate multiple variations and pick the best

**Won't load in browser?**
- Check Console (F12) for errors
- Verify file size < 50 MB
- Try re-exporting from 3D generator

---

## Alternative: Use Pre-made Indian Doctor Models

If the above is too complex, search these free model sites:
- **Sketchfab**: https://sketchfab.com/search?q=indian+doctor&type=models (Filter: Downloadable)
- **CGTrader Free**: https://www.cgtrader.com/free-3d-models (Search: "Indian doctor")
- **TurboSquid Free**: https://www.turbosquid.com/ (Filter: Free)
- **Quaternius**: https://quaternius.com/ (Stylized doctor models)

---

## Need Help?

1. Generate image first, share the URL
2. I'll help with 3D conversion
3. I'll integrate it into your project

Let me know when you're ready! 🎨
