from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import speech_recognition as sr
import tempfile
import os
import uvicorn
from deep_translator import GoogleTranslator



app = FastAPI()

# Serve icons and manifest
app.mount("/icons", StaticFiles(directory="icons"), name="icons")

@app.get("/manifest.json")
async def manifest():
    return FileResponse("manifest.json", media_type="application/manifest+json")

@app.get("/", response_class=HTMLResponse)
async def get_index():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
        <title>Audio Translator</title>
        <link rel="manifest" href="/manifest.json">
        <link rel="icon" href="/icons/icon-192.png">
        <style>
            body { font-family: Arial; text-align: center; padding: 40px; }
            button { padding: 10px 20px; font-size: 16px; }
            select, textarea { font-size: 16px; padding: 8px; }
        </style>
    </head>
    <body>
        <h2>🎙️ Audio Recorder & Translator</h2>

        <label>From: </label>
        <select id="inputLang">
            <option value="en">English</option>
            <option value="ta">Tamil</option>
            <option value="hi">Hindi</option>
            <option value="fr">French</option>
        </select>

        <label> → To: </label>
        <select id="outputLang">
            <option value="ta">Tamil</option>
            <option value="en">English</option>
            <option value="hi">Hindi</option>
            <option value="fr">French</option>
        </select>
        <br/><br/>

        <button id="startBtn" disabled>Start Recording</button>
        <button id="stopBtn" class="red">Stop & Translate</button>
        <p id="status"></p>
        <audio id="audio" controls></audio>

        <h3>📝 Transcription:</h3>
        <textarea id="result" rows="3" cols="50"></textarea>

        <h3>🌐 Translation:</h3>
        <textarea id="translated" rows="3" cols="50"></textarea>

        <script>
            let mediaRecorder;
            let audioChunks = [];

            navigator.mediaDevices.getUserMedia({ audio: true })
                .then(stream => {
                    mediaRecorder = new MediaRecorder(stream);
                    document.getElementById("startBtn").disabled = false;

                    mediaRecorder.ondataavailable = e => audioChunks.push(e.data);

                    mediaRecorder.onstop = () => {
                        const blob = new Blob(audioChunks, { type: 'audio/mp3' });
                        document.getElementById("audio").src = URL.createObjectURL(blob);

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
                        })
                        .catch(err => {
                            document.getElementById("result").value = "Error: " + err;
                        });

                        audioChunks = [];
                    };
                });

            document.getElementById("startBtn").addEventListener("click", () => {
                audioChunks = [];
                mediaRecorder.start();
                document.getElementById("status").innerText = "Recording...";
            });

            document.getElementById("stopBtn").addEventListener("click", () => {
                mediaRecorder.stop();
                document.getElementById("status").innerText = "Processing...";
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

        # Translate
        translated_text = GoogleTranslator(source=input_lang, target=output_lang).translate(text)


        return {"transcription": text, "translation": translated_text}

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
