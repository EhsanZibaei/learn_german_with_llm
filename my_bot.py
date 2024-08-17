import sounddevice as sd
import numpy as np
import wavio
import threading
import openai
import os
from flask import Flask
import pygame
import warnings
import os
import sys
from env.openai_key import API_KEY


# Disable all warnings
warnings.filterwarnings("ignore")

# Initialize Flask app
app = Flask(__name__)

# Set OpenAI API key from environment variable
# os.environ["OPENAI_API_KEY"] = "sk-proj-8YRtQ2g78yEpie422xq0T3BlbkFJrdLcp2o0a9tgesvq4KNG"
openai.api_key = os.getenv(API_KEY)

# audio to text
def audio_to_text():
    audio_file = open("ehsan.wav", "rb")
    transcription = openai.Audio.transcribe(
        model="whisper-1",
        file=audio_file,
        response_format="text",
        language="de"
    )
    print("---------ehsan says: " + transcription['text'])
    return transcription['text']

# send chatgpt request
def send_request(question_text):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": "erts umformuliere mein satz auf mutterschprachlier deuscth form. dann die gespräsch fortführen."
            },
            {
                "role": "user",
                "content": "das ist mein satz " + question_text
            }
        ],
        temperature=0.1,
        max_tokens=94,
        top_p=1
    )
    print("*********chatgpt says:" + response.choices[0].message['content'] + "\n")
    return response.choices[0].message['content']

# text to audio
def text_to_audio(text):
    speech_file_path = "chatgpt.mp3"
    response_voice = openai.Audio.create(
        model="tts-1",
        voice="alloy",
        input=text
    )
    with open(speech_file_path, 'wb') as f:
        f.write(response_voice['audio'])
    return speech_file_path

# play audio
def play_audio(file_path):
    pygame.init()
    pygame.mixer.init()
    my_sound = pygame.mixer.Sound(file_path)
    my_sound.play()

# function to continuously listen to user and reply
@app.route("/")
def listen_respond():
    fs = 44100  # Sample rate
    channels = 2  # Number of audio channels
    dtype = 'int16'  # Data type

    recording = []
    is_recording = False

    def record_audio():
        nonlocal recording, is_recording
        recording = []
        while is_recording:
            audio = sd.rec(int(fs * 0.5), samplerate=fs, channels=channels, dtype=dtype)
            sd.wait()
            recording.append(audio)

    def start_recording():
        nonlocal is_recording
        is_recording = True
        threading.Thread(target=record_audio).start()
        print("Recording started...")

    def stop_recording():
        nonlocal is_recording
        is_recording = False
        print("Recording stopped.\n")
        audio_data = np.concatenate(recording, axis=0)
        wavio.write("ehsan.wav", audio_data, fs, sampwidth=2)

    while True:
        command = input("Press 'r' to start recording, 's' to stop recording, or 'q' to quit: ")
        if command.lower() == 'r':
            start_recording()
        elif command.lower() == 's':
            stop_recording()
            question_text = audio_to_text()
            response_text = send_request(question_text)
            response_voice = text_to_audio(response_text)
            play_audio(response_voice)
        elif command.lower() == 't':
            play_audio("chatgpt.mp3")
        elif command.lower() == 'q':
            if is_recording:
                stop_recording()
            break
        else:
            print("Invalid command. Please press 'r' to start recording, 's' to stop recording, or 'q' to quit.")

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)
