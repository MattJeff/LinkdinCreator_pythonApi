import whisper
import openai
import yt_dlp
import os
from moviepy.editor import VideoFileClip
from datetime import timedelta
from flask import Flask, jsonify, request
import uuid

# Clés d'API
WHISPER_API_KEY = "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"
GPT4_API_KEY = "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"

openai.api_key = GPT4_API_KEY

# Chemins des fichiers
project_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "project_directory")
video_path = os.path.join(project_dir, "video.mp4")
audio_path = os.path.join(project_dir, "audio.mp3")
srt_path = os.path.join(project_dir, "subtitles.srt")

def download_video_from_youtube(url):
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4',
        'outtmpl': video_path
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

def extract_audio_from_video():
    video_clip = VideoFileClip(video_path)
    audio_clip = video_clip.audio
    audio_clip.write_audiofile(audio_path)
    audio_clip.close()
    video_clip.close()

def transcribe_audio():
    model = whisper.load_model('large')
    print("Whisper model loaded.")
    transcribe = model.transcribe(audio_path)
    segments = transcribe['segments']

    srt_data = ""
    for index, segment in enumerate(segments):
        startTime = str(timedelta(seconds=int(segment['start']))) + ",000"
        endTime = str(timedelta(seconds=int(segment['end']))) + ",000"
        text = segment['text']
        segment_data = f"{index+1}\n{startTime} --> {endTime}\n{text}\n\n"
        srt_data += segment_data

    with open(srt_path, 'w', encoding='utf-8') as srtFile:
        srtFile.write(srt_data)

    return srt_path

def summarize_conversation(srt_file):
    with open(srt_file, 'r') as file:
        srt_text = file.read()

    prompt = f"Résumez la conversation suivante :\n\n{srt_text}\n\nRésumé:"
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=2050
    )
    return response.choices[0].text.strip()

def create_linkedin_post(summary):
    prompt = f"fais un post LinkedIn basé sur le résumé suivant avec une accroche, des smylet des point et a la fin un call to action et une mise en forme  :\n\n{summary}\n\n"
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=2050
    )
    return response.choices[0].text.strip()

# Exemple d'utilisation:
#if __name__ == "__main__":
#    url = "https://youtube.com/shorts/lZPClCj4tRA?feature=share"
#    download_video_from_youtube(url)
#    extract_audio_from_video()
#    srt_file = transcribe_audio()
#    post = create_linkedin_post(summary)
#    print(post)

app = Flask(__name__)

# Endpoint pour envoyer des données
@app.route('/transcribe', methods=['POST'])
def transcribe_video():
    data = request.json
    if not data or 'url' not in data:
        return jsonify({"error": "URL manquante"}), 400

    url = data['url']

    # Télécharge la vidéo et extrait l'audio
    download_video_from_youtube(url)
    extract_audio_from_video()

    # Transcrit l'audio en texte
    srt_file = transcribe_audio()

    # Résume la conversation
    summary = summarize_conversation(srt_file)

    # Crée un post LinkedIn
    post = create_linkedin_post(summary)

    return jsonify({
        "id": str(uuid.uuid4()), # Vous pouvez générer un ID unique ici si nécessaire
        "url": url,
        "transcription": open(srt_file, 'r').read(),
        "summary": summary,
        "linkedinPost": post
    })

if __name__ == "__main__":
    app.run(debug=True)
