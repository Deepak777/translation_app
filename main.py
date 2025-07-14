from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import speech_recognition as sr
import tempfile
import os
import uvicorn

import google.generativeai as genai
import time
from google.api_core import exceptions
from google.generativeai import GenerativeModel, configure

API_KEYS = [
    "AIzaSyBpArcU5RuYvhAk3c9X8nsZrXodjMlyxpo",
    "AIzaSyB-RajV0491qW08VDJlQDBRCKmd4UslYYA",  # Key 1
    "AIzaSyB4cqEqYw1LwjuFry6dHa_1ih4pcbwYIig",
    "AIzaSyD3iyBt46-ETNTAfLXIbhVXKHg4FyBZUA0",
    "AIzaSyALibZJnx78ockCJQn41KOIA7q90bZxtbo",
    "AIzaSyDLm1c3fnjUxbGoH0bockku1_G_1_EBkuM",
    "AIzaSyCUzfYVJME2Z6xF0gO6gtVaDFHgzZB2FuM",
    "AIzaSyAgjYlTj-e_sX_Bvi8MoX4z6CoCfEYy2hw",
    "AIzaSyCZPlyOQei-h_7hQ1kzS7EwsYmTC2IFpwM",
    "AIzaSyA52MEtu3duLlKFrSrjseTIZczNSBhVaEU",
    "AIzaSyA4YfkLcPKY4oTAZQ15XKU0FIUwW3eNYow",
    "AIzaSyCGTE0GmdmEN-hCz1Vh1pQo4O1ZH8IJEkY",
    "AIzaSyCR7IbpxZl0GECaWk2aa4XmBiW8p_GtUvM",
    "AIzaSyDvHnys_Vy-ExTJyOegKawUOnbIvmswbPU",
    "AIzaSyAu_6iQS1yR0dYF_iFLCvUu_t-aSmd_QoQ"    # Key 3
]

current_key_index = 0
configure(api_key=API_KEYS[current_key_index])

def rotate_api_key():
    global current_key_index
    current_key_index = (current_key_index + 1) % len(API_KEYS)
    configure(api_key=API_KEYS[current_key_index])
    print(f"🔁 Switched to API key {current_key_index + 1}")

def get_gemini_model():
    return GenerativeModel("gemini-1.5-flash")

def handle_api_error(func):
    def wrapper(*args, **kwargs):
        max_retries = len(API_KEYS) * 2
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)

            except exceptions.ResourceExhausted as e:
                print(f"⚠️ Quota exhausted. Rotating... Attempt {attempt + 1}")
                rotate_api_key()
                time.sleep(getattr(e, "retry_delay", 5))

            except exceptions.PermissionDenied as e:
                print(f"🚫 Permission denied (maybe 429). Rotating... Attempt {attempt + 1}")
                rotate_api_key()
                time.sleep(10)

            except Exception as e:
                if "429" in str(e) or "quota" in str(e).lower():
                    print(f"⚠️ Generic 429/quota error. Rotating... Attempt {attempt + 1}")
                    rotate_api_key()
                    time.sleep(5)
                else:
                    raise

        raise Exception("❌ All API keys exhausted.")
    return wrapper

@handle_api_error
def gemini_translate(text, target_lang):
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = f"""
    You are an expert in multilingual text normalization and translation.

    The following sentence contains **mixed languages** (like Tamil, English, Hindi, etc.), but some foreign words may be written **phonetically using a different script** (e.g., English words in Tamil letters, or Hindi in Latin script).

    Your task:
    1. Detect and restore phonetically written foreign words to their correct original spelling.
    2. Then translate the cleaned-up text into '{target_lang}'.

    Respond with only the final translated result.

    Here is the input:
    {text}
    """
    response = model.generate_content(prompt)
    return response.text.strip()




app = FastAPI()

@app.get("/manifest.json")
async def manifest():
    return FileResponse("manifest.json", media_type="application/manifest+json")

app.mount("/.well-known", StaticFiles(directory=".well-known"), name="well-known")

@app.get("/", response_class=HTMLResponse)
async def get_index():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
        <title>🎙️ Audio Translator</title>
        <link rel="manifest" href="/manifest.json">
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600&display=swap" rel="stylesheet">
        <style>
            :root {
                --primary: #4361ee;
                --primary-light: #4895ef;
                --secondary: #3f37c9;
                --dark: #1e1e24;
                --light: #f8f9fa;
                --success: #4cc9f0;
                --danger: #f72585;
                --warning: #f8961e;
                --border-radius: 12px;
                --shadow: 0 10px 20px rgba(0,0,0,0.1);
                --transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
            }
            
            * {
                box-sizing: border-box;
                margin: 0;
                padding: 0;
            }
            
            body {
                font-family: 'Poppins', sans-serif;
                background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                min-height: 100vh;
                padding: 2rem;
                color: var(--dark);
                line-height: 1.6;
            }
            
            .container {
                max-width: 800px;
                margin: 0 auto;
                background: white;
                border-radius: var(--border-radius);
                box-shadow: var(--shadow);
                padding: 2rem;
                position: relative;
                overflow: hidden;
                animation: fadeIn 0.5s ease-out;
            }
            
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(20px); }
                to { opacity: 1; transform: translateY(0); }
            }
            
            h2 {
                color: var(--primary);
                margin-bottom: 1.5rem;
                font-weight: 600;
                text-align: center;
                position: relative;
                padding-bottom: 1rem;
            }
            
            h2::after {
                content: '';
                position: absolute;
                bottom: 0;
                left: 50%;
                transform: translateX(-50%);
                width: 80px;
                height: 4px;
                background: var(--primary-light);
                border-radius: 2px;
            }
            
            .language-selectors {
                display: flex;
                justify-content: center;
                align-items: center;
                flex-wrap: wrap;
                gap: 1rem;
                margin-bottom: 2rem;
            }
            
            .language-selector {
                display: flex;
                flex-direction: column;
                align-items: center;
            }
            
            .language-selector label {
                font-weight: 500;
                margin-bottom: 0.5rem;
                color: var(--dark);
            }
            
            select {
                font-family: inherit;
                font-size: 16px;
                padding: 0.8rem 1.2rem;
                border: 2px solid #e9ecef;
                border-radius: var(--border-radius);
                background: white;
                color: var(--dark);
                cursor: pointer;
                transition: var(--transition);
                min-width: 150px;
                appearance: none;
                background-image: url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3e%3cpolyline points='6 9 12 15 18 9'%3e%3c/polyline%3e%3c/svg%3e");
                background-repeat: no-repeat;
                background-position: right 1rem center;
                background-size: 1em;
            }
            
            select:focus {
                outline: none;
                border-color: var(--primary-light);
                box-shadow: 0 0 0 3px rgba(67, 97, 238, 0.2);
            }
            
            .controls {
                display: flex;
                justify-content: center;
                gap: 1rem;
                margin-bottom: 2rem;
                flex-wrap: wrap;
            }
            
            button {
                font-family: inherit;
                font-size: 1rem;
                font-weight: 500;
                padding: 0.8rem 1.8rem;
                border-radius: var(--border-radius);
                border: none;
                cursor: pointer;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                gap: 0.5rem;
                transition: var(--transition);
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }
            
            button:hover {
                transform: translateY(-2px);
                box-shadow: 0 7px 14px rgba(0, 0, 0, 0.1);
            }
            
            button:active {
                transform: translateY(0);
            }
            
            button:disabled {
                opacity: 0.6;
                cursor: not-allowed;
                transform: none !important;
            }
            
            .btn-primary {
                background-color: var(--primary);
                color: white;
            }
            
            .btn-primary:hover {
                background-color: var(--primary-light);
            }
            
            .btn-secondary {
                background-color: white;
                color: var(--primary);
                border: 2px solid var(--primary);
            }
            
            .btn-secondary:hover {
                background-color: #f0f4ff;
            }
            
            .btn-danger {
                background-color: var(--danger);
                color: white;
            }
            
            .btn-danger:hover {
                background-color: #ff4785;
            }
            
            .btn-success {
                background-color: var(--success);
                color: white;
            }
            
            .btn-success:hover {
                background-color: #5fd4f7;
            }
            
            .status {
                text-align: center;
                margin: 1rem 0;
                font-weight: 500;
                min-height: 24px;
                transition: var(--transition);
            }
            
            .status.recording {
                color: var(--danger);
                animation: pulse 1.5s infinite;
            }
            
            @keyframes pulse {
                0% { opacity: 1; }
                50% { opacity: 0.6; }
                100% { opacity: 1; }
            }
            
            .status.success {
                color: var(--success);
            }
            
            .status.error {
                color: var(--danger);
            }
            
            .audio-container {
                display: flex;
                justify-content: center;
                margin: 1.5rem 0;
            }
            
            audio {
                width: 100%;
                max-width: 400px;
                border-radius: var(--border-radius);
                box-shadow: var(--shadow);
                transition: var(--transition);
            }
            
            audio:hover {
                box-shadow: 0 12px 24px rgba(0,0,0,0.1);
            }
            
            .result-container {
                margin: 2rem 0;
            }
            
            .result-box {
                margin-bottom: 2rem;
                animation: slideUp 0.4s ease-out;
            }
            
            @keyframes slideUp {
                from { opacity: 0; transform: translateY(20px); }
                to { opacity: 1; transform: translateY(0); }
            }
            
            .result-box h3 {
                margin-bottom: 0.8rem;
                color: var(--primary);
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }
            
            textarea {
                width: 100%;
                padding: 1rem;
                font-family: inherit;
                font-size: 1rem;
                border: 2px solid #e9ecef;
                border-radius: var(--border-radius);
                resize: vertical;
                min-height: 120px;
                transition: var(--transition);
            }
            
            textarea:focus {
                outline: none;
                border-color: var(--primary-light);
                box-shadow: 0 0 0 3px rgba(67, 97, 238, 0.2);
            }
            
            .download-buttons {
                display: flex;
                justify-content: center;
                gap: 1rem;
                margin-top: 1rem;
                flex-wrap: wrap;
            }
            
            .ripple {
                position: relative;
                overflow: hidden;
            }
            
            .ripple:after {
                content: "";
                display: block;
                position: absolute;
                width: 100%;
                height: 100%;
                top: 0;
                left: 0;
                pointer-events: none;
                background-image: radial-gradient(circle, #fff 10%, transparent 10.01%);
                background-repeat: no-repeat;
                background-position: 50%;
                transform: scale(10, 10);
                opacity: 0;
                transition: transform .5s, opacity 1s;
            }
            
            .ripple:active:after {
                transform: scale(0, 0);
                opacity: 0.3;
                transition: 0s;
            }
            
            @media (max-width: 600px) {
                body {
                    padding: 1rem;
                }
                
                .container {
                    padding: 1.5rem;
                }
                
                .controls {
                    flex-direction: column;
                    align-items: center;
                }
                
                button {
                    width: 100%;
                }
                
                .language-selectors {
                    flex-direction: column;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>🎙️ Audio Translator</h2>
            
            <div class="language-selectors">
                <div class="language-selector">
                    <label for="inputLang">Source Language</label>
                    <select id="inputLang">
                        <option value="en">English</option>
                        <option value="ta">Tamil</option>
                        <option value="hi">Hindi</option>
                        <option value="fr">French</option>
                        <option value="es">Spanish</option>
                        <option value="de">German</option>
                        <option value="ja">Japanese</option>
                        <option value="ko">Korean</option>
                    </select>
                </div>
                
                <div class="language-selector">
                    <label for="outputLang">Target Language</label>
                    <select id="outputLang">
                        <option value="ta">Tamil</option>
                        <option value="en">English</option>
                        <option value="hi">Hindi</option>
                        <option value="fr">French</option>
                        <option value="es">Spanish</option>
                        <option value="de">German</option>
                        <option value="ja">Japanese</option>
                        <option value="ko">Korean</option>
                    </select>
                </div>
            </div>
            
            <div class="controls">
                <button id="startBtn" class="btn-primary ripple" disabled>
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <circle cx="12" cy="12" r="10"></circle>
                        <polygon points="10 8 16 12 10 16 10 8"></polygon>
                    </svg>
                    Start Recording
                </button>
                <button id="stopBtn" class="btn-danger ripple">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <rect x="6" y="4" width="4" height="16"></rect>
                        <rect x="14" y="4" width="4" height="16"></rect>
                    </svg>
                    Stop & Translate
                </button>
            </div>
            
            <p id="status" class="status"></p>
            
            <div class="audio-container">
                <audio id="audio" controls></audio>
            </div>
            
            <div class="download-buttons">
                <button onclick="downloadAudio()" class="btn-secondary ripple">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                        <polyline points="7 10 12 15 17 10"></polyline>
                        <line x1="12" y1="15" x2="12" y2="3"></line>
                    </svg>
                    Download Audio
                </button>
            </div>
            
            <div class="result-container">
                <div class="result-box">
                    <h3>
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                        </svg>
                        Transcription
                    </h3>
                    <textarea id="result" rows="3" readonly></textarea>
                    <div class="download-buttons">
                        <button onclick="downloadText('result', 'transcription.txt')" class="btn-secondary ripple">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                                <polyline points="7 10 12 15 17 10"></polyline>
                                <line x1="12" y1="15" x2="12" y2="3"></line>
                            </svg>
                            Download Transcription
                        </button>
                    </div>
                </div>
                
                <div class="result-box">
                    <h3>
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <circle cx="12" cy="12" r="10"></circle>
                            <line x1="2" y1="12" x2="22" y2="12"></line>
                            <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path>
                        </svg>
                        Translation
                    </h3>
                    <textarea id="translated" rows="3" readonly></textarea>
                    <div class="download-buttons">
                        <button onclick="downloadText('translated', 'translation.txt')" class="btn-secondary ripple">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                                <polyline points="7 10 12 15 17 10"></polyline>
                                <line x1="12" y1="15" x2="12" y2="3"></line>
                            </svg>
                            Download Translation
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <script>
            let mediaRecorder;
            let audioChunks = [];
            let stream;
            let isRecording = false;

            document.getElementById("startBtn").addEventListener("click", async () => {
                try {
                    // Request mic access
                    stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                    mediaRecorder = new MediaRecorder(stream);
                    audioChunks = [];

                    // Update UI
                    document.getElementById("stopBtn").disabled = false;
                    document.getElementById("startBtn").disabled = true;
                    document.getElementById("status").innerText = "Recording...";
                    document.getElementById("status").className = "status recording";
                    
                    // Add animation class to container
                    document.querySelector(".container").classList.add("recording-active");

                    mediaRecorder.ondataavailable = e => audioChunks.push(e.data);

                    mediaRecorder.onstop = () => {
                        // Stop the microphone
                        stream.getTracks().forEach(track => track.stop());

                        const blob = new Blob(audioChunks, { type: 'audio/mp3' });
                        const audioURL = URL.createObjectURL(blob);
                        document.getElementById("audio").src = audioURL;

                        const formData = new FormData();
                        formData.append('audio_file', blob, 'recording.mp3');
                        formData.append('input_lang', document.getElementById("inputLang").value);
                        formData.append('output_lang', document.getElementById("outputLang").value);

                        fetch('/upload-audio', {
                            method: 'POST',
                            body: formData
                        })
                        .then(res => res.json())
                        .then(data => {
                            document.getElementById("result").value = data.transcription || "Error";
                            document.getElementById("translated").value = data.translation || "Error";
                            document.getElementById("status").innerText = "✅ Translation complete!";
                            document.getElementById("status").className = "status success";
                            
                            // Animate result boxes
                            document.querySelectorAll(".result-box").forEach(box => {
                                box.style.animation = "none";
                                setTimeout(() => {
                                    box.style.animation = "slideUp 0.4s ease-out";
                                }, 10);
                            });
                        })
                        .catch(err => {
                            document.getElementById("result").value = "Error: " + err;
                            document.getElementById("status").innerText = "❌ Translation failed";
                            document.getElementById("status").className = "status error";
                        });

                        // Reset
                        audioChunks = [];
                        document.getElementById("stopBtn").disabled = true;
                        document.getElementById("startBtn").disabled = false;
                        document.querySelector(".container").classList.remove("recording-active");
                    };

                    mediaRecorder.start();
                    isRecording = true;
                } catch (err) {
                    document.getElementById("status").innerText = "Microphone error: " + err.message;
                    document.getElementById("status").className = "status error";
                }
            });

            document.getElementById("stopBtn").addEventListener("click", () => {
                if (mediaRecorder && isRecording) {
                    mediaRecorder.stop();
                    document.getElementById("status").innerText = "Processing...";
                    document.getElementById("status").className = "status";
                    isRecording = false;
                }
            });

            function downloadAudio() {
                const audio = document.getElementById("audio");
                if (!audio.src) {
                    alert("No audio available to download");
                    return;
                }
                const a = document.createElement("a");
                a.href = audio.src;
                a.download = "recording.mp3";
                a.click();
            }

            function downloadText(id, filename) {
                const text = document.getElementById(id).value;
                if (!text) {
                    alert("No text available to download");
                    return;
                }
                const blob = new Blob([text], { type: 'text/plain' });
                const a = document.createElement("a");
                a.href = URL.createObjectURL(blob);
                a.download = filename;
                a.click();
            }

            // Enable start button when page loads
            window.addEventListener('load', () => {
                document.getElementById("startBtn").disabled = false;
            });
        </script>
    </body>
    </html>
    """

@app.post("/upload-audio")
async def upload_audio(
    audio_file: UploadFile = File(...),
    input_lang: str = Form(...),
    output_lang: str = Form(...)
):
    try:
        # Save mp3 to temp
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio:
            temp_audio.write(await audio_file.read())
            mp3_path = temp_audio.name

        # Convert to WAV using ffmpeg
        wav_path = mp3_path.replace(".mp3", ".wav")
        os.system(f'ffmpeg -y -i "{mp3_path}" "{wav_path}"')

        # Speech recognition
        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio = recognizer.record(source)
            text = recognizer.recognize_google(audio, language=input_lang)

        # Translate using googletrans
        translated_text = gemini_translate(text, output_lang)


        return {"transcription": text, "translation": translated_text}

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000)
