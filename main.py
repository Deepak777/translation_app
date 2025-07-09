


from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
import speech_recognition as sr
import tempfile
import os
import uvicorn

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
async def get_index():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="manifest" href="manifest.json">

        <title>Audio Recorder with Speech Recognition</title>
        <style>
            body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
            button { font-size: 16px; padding: 10px 20px; margin: 10px; }
            .red { background-color: #ff4444; color: white; }
        </style>
    </head>
    <body>
        <h1>Audio Recorder with Speech Recognition</h1>
        <button id="startBtn" disabled>Start Recording</button>
        <button id="stopBtn" class="red">Stop & Process</button>
        <p id="status"></p>
        <audio id="audio" controls></audio>
        <h3>Recognition Result:</h3>
        <textarea id="result" rows="4" cols="50"></textarea>

        <script>
            let mediaRecorder;
            let audioChunks = [];

            navigator.mediaDevices.getUserMedia({ audio: true })
                .then(stream => {
                    mediaRecorder = new MediaRecorder(stream);
                    document.getElementById("startBtn").disabled = false;

                    mediaRecorder.ondataavailable = event => {
                        audioChunks.push(event.data);
                    };

                    mediaRecorder.onstop = () => {
                        const audioBlob = new Blob(audioChunks, { type: 'audio/mp3' });
                        const audioUrl = URL.createObjectURL(audioBlob);
                        document.getElementById("audio").src = audioUrl;

                        const formData = new FormData();
                        formData.append('audio_file', audioBlob, 'recording.mp3');

                        fetch('/upload-audio', {
                            method: 'POST',
                            body: formData
                        })
                        .then(response => response.json())
                        .then(data => {
                            document.getElementById("result").value = data.transcription || data.error;
                        })
                        .catch(error => {
                            document.getElementById("result").value = "Error: " + error;
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
async def upload_audio(audio_file: UploadFile = File(...)):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio:
            temp_audio.write(await audio_file.read())
            temp_audio_path = temp_audio.name

        wav_path = temp_audio_path.replace(".mp3", ".wav")
        os.system(f'ffmpeg -i "{temp_audio_path}" "{wav_path}"')

        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio = recognizer.record(source)
            text = recognizer.recognize_google(audio)

        return {"transcription": text}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
