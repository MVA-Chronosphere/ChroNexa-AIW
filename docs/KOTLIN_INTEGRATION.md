# Kotlin / Temi Robot — Avatar Integration Guide

This guide explains how to integrate the ChroNexa 3D avatar into a Kotlin-based temi robot application. The avatar is a self-contained web component that renders in a WebView and is controlled via JavaScript `postMessage` calls.

---

## 1. Clone the Repository

```bash
git clone https://github.com/MVA-Chronosphere/ChroNexa-AIW.git
cd ChroNexa-AIW
```

---

## 2. Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│  Temi Robot (Kotlin App)                            │
│                                                     │
│  ┌──────────────┐     ┌──────────────────────────┐  │
│  │ Your Kotlin  │────►│ WebView                  │  │
│  │ Backend      │     │  ┌────────────────────┐  │  │
│  │ (Ollama,     │     │  │ avatar-view.html   │  │  │
│  │  Temi SDK,   │     │  │ ┌────────────────┐ │  │  │
│  │  KB, TTS)    │     │  │ │ Three.js Scene │ │  │  │
│  │              │     │  │ │ + HeadAudio     │ │  │  │
│  │              │     │  │ │ + Lip Sync      │ │  │  │
│  │              │     │  │ └────────────────┘ │  │  │
│  └──────┬───────┘     │  └────────────────────┘  │  │
│         │             └──────────────────────────┘  │
│         │ postMessage(audio + cues)                 │
│         └───────────────────────────────────────────┘
```

**Key concept:** The avatar is a single HTML file (`avatar-view.html`) loaded in an Android `WebView`. Your Kotlin code sends it audio + lip sync data via JavaScript, and the avatar speaks with synchronized mouth movements and hand gestures automatically.

---

## 3. Files You Need (Avatar Only)

Copy these files from the repo into your Kotlin project's `assets/` folder:

```
assets/
├── avatar-view.html              ← Main avatar renderer (Three.js)
├── indian_doctor_lipsync.glb     ← 3D avatar model (19.5 MB)
└── headaudio/
    ├── headaudio.min.mjs         ← Real-time audio lip sync engine
    └── headworklet.min.mjs       ← AudioWorklet processor
```

Source locations in the repo:
- `frontend/public/avatar-view.html`
- `frontend/public/indian_doctor_lipsync.glb`
- `frontend/public/headaudio/headaudio.min.mjs`
- `frontend/public/headaudio/headworklet.min.mjs`

---

## 4. WebView Setup (Kotlin)

### 4.1 Add WebView to your layout

```xml
<!-- res/layout/activity_avatar.xml -->
<WebView
    android:id="@+id/avatarWebView"
    android:layout_width="match_parent"
    android:layout_height="match_parent" />
```

### 4.2 Configure WebView in Activity/Fragment

```kotlin
import android.webkit.WebView
import android.webkit.WebSettings
import android.webkit.WebChromeClient
import android.webkit.WebViewClient

class AvatarActivity : AppCompatActivity() {

    private lateinit var avatarWebView: WebView

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_avatar)

        avatarWebView = findViewById(R.id.avatarWebView)
        setupWebView()
    }

    private fun setupWebView() {
        avatarWebView.apply {
            settings.javaScriptEnabled = true
            settings.domStorageEnabled = true
            settings.mediaPlaybackRequiresUserGesture = false  // allow auto-play audio
            settings.allowFileAccess = true
            settings.allowContentAccess = true
            settings.mixedContentMode = WebSettings.MIXED_CONTENT_ALWAYS_ALLOW

            webChromeClient = WebChromeClient()
            webViewClient = WebViewClient()

            // Load avatar from assets
            loadUrl("file:///android_asset/avatar-view.html")
        }
    }
}
```

> **Important:** `mediaPlaybackRequiresUserGesture = false` is required so the avatar can play audio through the HeadAudio system without user tapping.

### 4.3 Fix asset paths in avatar-view.html

Since the file loads from `file:///android_asset/`, update the model and HeadAudio paths in `avatar-view.html`:

Find these lines and change them:

```javascript
// BEFORE (web server paths)
loader.load('/indian_doctor_lipsync.glb', ...
await audioCtx.audioWorklet.addModule('/headaudio/headworklet.min.mjs');
const { HeadAudio } = await import('/headaudio/headaudio.min.mjs');
await headAudio.loadModel('/headaudio/model-en-mixed.bin');

// AFTER (Android asset paths)
loader.load('indian_doctor_lipsync.glb', ...
await audioCtx.audioWorklet.addModule('headaudio/headworklet.min.mjs');
const { HeadAudio } = await import('headaudio/headaudio.min.mjs');
await headAudio.loadModel('headaudio/model-en-mixed.bin');
```

Just remove the leading `/` from all paths — relative paths resolve correctly from `file:///android_asset/`.

---

## 5. Sending Audio to the Avatar (Lip Sync)

### 5.1 Primary Method: Audio-Driven (HeadAudio)

This is the **recommended** approach. Send a base64 audio data URI and the avatar automatically analyzes the audio waveform in real-time to drive lip movements. No pre-computed lip sync cues needed.

```kotlin
/**
 * Make the avatar speak with real-time audio-driven lip sync.
 *
 * @param audioBase64 Base64-encoded audio (mp3 or wav)
 * @param mimeType    "audio/mpeg" for mp3, "audio/wav" for wav
 */
fun speakWithAudio(audioBase64: String, mimeType: String = "audio/mpeg") {
    val audioDataUri = "data:$mimeType;base64,$audioBase64"

    val js = """
        window.postMessage({
            type: 'playAudioWithLipSync',
            audioUrl: '$audioDataUri',
            _mouthCues: []
        }, '*');
    """.trimIndent()

    avatarWebView.evaluateJavascript(js, null)
}
```

**How it works:**
1. HeadAudio decodes the audio and plays it via `AudioContext`
2. An AudioWorklet analyzes frequency content in real-time
3. Viseme weights (mouth shapes) are computed and applied to the 3D model
4. Hand gestures start automatically for the speech duration

### 5.2 Fallback Method: Cue-Based Lip Sync (Rhubarb)

If you have pre-computed Rhubarb lip sync cues (from the ChroNexa backend), send them as a fallback. HeadAudio is tried first; cues are used only if HeadAudio fails.

```kotlin
/**
 * Make the avatar speak with pre-computed mouth cues.
 *
 * @param audioBase64 Base64-encoded audio
 * @param mouthCues   JSON array of Rhubarb cues: [{"start":0.0,"end":0.5,"value":"A"}, ...]
 */
fun speakWithCues(
    audioBase64: String,
    mouthCues: String,
    mimeType: String = "audio/mpeg"
) {
    val audioDataUri = "data:$mimeType;base64,$audioBase64"

    val js = """
        window.postMessage({
            type: 'playAudioWithLipSync',
            audioUrl: '$audioDataUri',
            _mouthCues: $mouthCues
        }, '*');
    """.trimIndent()

    avatarWebView.evaluateJavascript(js, null)
}
```

**Rhubarb mouth cue format:**
```json
[
  { "start": 0.00, "end": 0.15, "value": "X" },
  { "start": 0.15, "end": 0.40, "value": "D" },
  { "start": 0.40, "end": 0.65, "value": "C" },
  { "start": 0.65, "end": 0.80, "value": "B" },
  { "start": 0.80, "end": 1.00, "value": "X" }
]
```

Rhubarb shapes: `A`=MBP, `B`=EE, `C`=EH, `D`=AI, `E`=OH, `F`=OO, `G`=FV, `H`=L/TH, `X`=silence

---

## 6. Listening for Avatar Events

The avatar sends messages back when audio finishes:

```kotlin
// Add a JavaScript interface to receive messages from the avatar
avatarWebView.addJavascriptInterface(object {
    @JavascriptInterface
    fun onAvatarEvent(type: String) {
        runOnUiThread {
            when (type) {
                "audioEnded" -> {
                    // Avatar finished speaking
                    Log.d("Avatar", "Speech finished")
                    onSpeechComplete()
                }
            }
        }
    }
}, "AndroidBridge")
```

Then add this at the bottom of `avatar-view.html` (inside the `<script>` tag):

```javascript
// Forward audioEnded events to Kotlin
window.addEventListener('message', (event) => {
    if (event.data?.type === 'audioEnded' && window.AndroidBridge) {
        window.AndroidBridge.onAvatarEvent('audioEnded');
    }
});
```

---

## 7. Typical Integration Flow with Your Ollama Backend

```
User speaks → Temi ASR → text
                           │
                           ▼
              ┌─────────────────────┐
              │ Your Kotlin backend │
              │ (Ollama / KB query) │
              └──────────┬──────────┘
                         │ response text
                         ▼
              ┌─────────────────────┐
              │ TTS (Edge-TTS or    │
              │ Temi built-in TTS)  │
              └──────────┬──────────┘
                         │ audio bytes
                         ▼
              ┌─────────────────────┐
              │ Base64 encode audio │
              └──────────┬──────────┘
                         │
                         ▼
              avatarWebView.evaluateJavascript(
                  postMessage({ type: 'playAudioWithLipSync', audioUrl: dataUri })
              )
                         │
                         ▼
              ┌─────────────────────┐
              │ Avatar speaks with  │
              │ lip sync + gestures │
              └─────────────────────┘
```

### Example: Full pipeline in Kotlin

```kotlin
class TemiAvatarController(
    private val webView: WebView,
    private val ollamaClient: OllamaClient  // your Ollama HTTP client
) {
    /**
     * Process user input end-to-end:
     * 1. Send to Ollama for response
     * 2. Convert response to speech
     * 3. Send audio to avatar for lip-synced playback
     */
    suspend fun processUserInput(userText: String) {
        // 1. Get LLM response from your Ollama backend
        val response = ollamaClient.generate(
            model = "llama3:8b",
            prompt = userText
        )

        // 2. Generate TTS audio (use Edge-TTS, Google TTS, or Temi's built-in)
        val audioBytes = ttsService.synthesize(
            text = response.text,
            voice = "en-IN-NeerjaNeural"  // Indian English female
        )

        // 3. Send to avatar
        val audioBase64 = Base64.encodeToString(audioBytes, Base64.NO_WRAP)
        withContext(Dispatchers.Main) {
            speakWithAudio(audioBase64)
        }
    }

    private fun speakWithAudio(audioBase64: String) {
        val js = """
            window.postMessage({
                type: 'playAudioWithLipSync',
                audioUrl: 'data:audio/mpeg;base64,$audioBase64',
                _mouthCues: []
            }, '*');
        """.trimIndent()
        webView.evaluateJavascript(js, null)
    }
}
```

---

## 8. Optional: Use the ChroNexa Backend `/api/chat/animate` Endpoint

If you prefer to use the ChroNexa Python backend for lip sync generation (Rhubarb), there's a dedicated endpoint:

**POST** `http://<backend-host>:8000/api/chat/animate`

```json
// Request
{
    "audio_base64": "<base64-encoded-audio>",
    "mime_type": "audio/mpeg",
    "text": "optional transcript for better lip sync accuracy"
}

// Response
{
    "status": "success",
    "audio_data": "data:audio/mpeg;base64,...",
    "audio_duration": 3.5,
    "mouth_cues": [
        { "start": 0.0, "end": 0.15, "value": "X" },
        { "start": 0.15, "end": 0.4, "value": "D" },
        ...
    ]
}
```

Kotlin usage:
```kotlin
// Send your TTS audio to ChroNexa backend for lip sync cue generation
val animateResponse = httpClient.post("http://10.0.0.5:8000/api/chat/animate") {
    contentType(ContentType.Application.Json)
    setBody("""{"audio_base64":"$audioB64","mime_type":"audio/mpeg","text":"$responseText"}""")
}
val body = animateResponse.body<AnimateResponse>()

// Send audio + cues to avatar
speakWithCues(audioB64, Gson().toJson(body.mouthCues))
```

> **Note:** This endpoint requires Rhubarb to be installed on the backend. If you're only using HeadAudio (recommended), you don't need the ChroNexa backend at all — just the 4 frontend files.

---

## 9. Avatar Message API Reference

### Messages you send TO the avatar (`postMessage`):

| Message Type | Fields | Description |
|---|---|---|
| `playAudioWithLipSync` | `audioUrl: string`, `_mouthCues: array` | Play audio with lip sync (HeadAudio primary, cues fallback). Hand gestures auto-triggered. |
| `lipSync` | `mouthCues: array` | Start cue-based lip sync only (no audio playback). |
| `avatarSpeak` | `duration: number` | Simple head bob animation (basic fallback). |

### Messages the avatar sends BACK (`postMessage` to parent):

| Message Type | Description |
|---|---|
| `audioEnded` | Audio playback finished, avatar returned to idle. |

---

## 10. Troubleshooting

| Issue | Solution |
|---|---|
| Avatar blank / white screen | Check WebView JavaScript is enabled. Check browser console for GLB load errors. Verify asset paths have no leading `/`. |
| No sound | Set `mediaPlaybackRequiresUserGesture = false`. Ensure `AudioContext` is allowed (may need a user gesture first on some Android versions). |
| Lip sync not moving | Verify the GLB model has Oculus viseme morph targets (the provided `indian_doctor_lipsync.glb` does). Check HeadAudio init logs in console. |
| Audio plays but no lip movement | HeadAudio may have failed to init. Check console for `[HeadAudio] Init failed`. Provide `_mouthCues` as fallback. |
| Model too large for memory | The GLB is 19.5MB. On low-memory devices, consider using `renderer.setPixelRatio(1)` and reducing canvas size. |
| CORS errors in WebView | Use `file:///android_asset/` scheme. If loading from a local server, add `Access-Control-Allow-Origin: *`. |

---

## 11. Summary: What Goes Where

| Component | Owner | Where It Lives |
|---|---|---|
| 3D Avatar (WebView) | This repo | Kotlin `assets/` → `WebView` |
| Ollama LLM | Other developer | Kotlin backend / local server |
| Knowledge Base | Other developer | Strapi / custom backend |
| Temi Robot SDK | Other developer | Kotlin native |
| TTS | Either | Edge-TTS (Python) or Temi built-in |
| Lip Sync | HeadAudio (automatic) | Runs inside `avatar-view.html` |
