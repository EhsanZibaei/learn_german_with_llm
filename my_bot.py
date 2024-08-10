import sounddevice as sd
import numpy as np
import wavio
import threading
from openai import OpenAI
import os
from IPython.display import Audio, Markdown, display
import pygame
import warnings
import openai

# Disable all warnings
warnings.filterwarnings("ignore")

# audio to text
def audio_to_text():
  

  audio_file= open("ehsan.wav", "rb")
  transcription = client.audio.transcriptions.create(
    model="whisper-1", 
    file=audio_file,
    response_format="text"
  )
  print("---------ehsan says: " + transcription)
  return transcription

# send chatgpt request
def send_request(question_text,client):

  response = client.chat.completions.create(
    model="gpt-4",
    messages=[
      {
        "role": "system",
        "content": "Du bekommst einen Satz auf Deutsch. Wenn der Satz mit dem Wort \"Frage\" beginnt, dann antworte nur auf die Frage. Andernfalls: Formuliere den Satz zuerst in umgangssprachlichem und lockerem Deutsch um. Danach führe das Gespräch weiter."
      },
      {
        "role": "user",
        "content": question_text
      }
    ],
    temperature=0.7,
    max_tokens=64,
    top_p=1
  )
  print ("*********chatgpt says:" + response.choices[0].message.content +"\n")
  return response.choices[0].message.content

# text to audio
def text_to_audio(text,client):

  speech_file_path = "chatgpt.mp3"
  response_voice = client.audio.speech.create(
    model="tts-1",
    voice="alloy",
    input=text
  )
  print("aaaaaaa")
  #with open(speech_file_path, 'wb') as f:
    #f.write(response_voice.audio_content)
  response_voice.stream_to_file(speech_file_path)

  # play audio
def play_audio():
    pygame.init()
    my_sound = pygame.mixer.Sound('chatgpt.mp3')
    my_sound.play()

if __name__=="__main__":
    os.environ["OPENAI_API_KEY"] = "sk-proj-8YRtQ2g78yEpie422xq0T3BlbkFJrdLcp2o0a9tgesvq4KNG"
    MODEL_NAME = "gpt-4o"
    SEED = 42
    client = OpenAI()

    fs = 44100  # Sample rate
    channels = 2  # Number of audio channels
    dtype = 'int16'  # Data type

    recording = []
    is_recording = False

    def record_audio():
        global recording, is_recording
        recording = []
        while is_recording:
            audio = sd.rec(int(fs * 0.5), samplerate=fs, channels=channels, dtype=dtype)
            sd.wait()
            recording.append(audio)
            #recording = [audio]

    def start_recording():
        global is_recording
        is_recording = True
        threading.Thread(target=record_audio).start()
        print("Recording started...")

    def stop_recording():
        global is_recording
        is_recording = False
        print("Recording stopped.\n")
        #audio_data = []
        audio_data = np.concatenate(recording, axis=0)
        wavio.write("ehsan.wav", audio_data, fs, sampwidth=2)
        # print("Audio saved as output.wav")

    while True:
        command = input("Press 'r' to start recording, 's' to stop recording, or 'q' to quit: ")
        if command.lower() == 'r':
            start_recording()
        elif command.lower() == 's':
            stop_recording()
            question_text = audio_to_text()
            response_text = send_request(question_text,client)
            response_voice = text_to_audio(response_text,client)
            play_audio()
            #IPython.display.Audio("reply.mp3")
        elif command.lower() == 'q':
            if is_recording:
                stop_recording()
            break
        else:
            print("Invalid command. Please press 'r' to start recording, 's' to stop recording, or 'q' to quit.")
