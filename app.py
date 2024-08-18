from flask import Flask, render_template_string, render_template, send_from_directory
from flask import request
import os
from env.openai_key import API_KEY
import openai
from openai import OpenAI

app = Flask(__name__)

os.environ["OPENAI_API_KEY"] = API_KEY
OpenAI.api_key = os.getenv("OPENAI_API_KEY")
MODEL_NAME = "gpt-4o"
SEED = 42
client = openai.OpenAI()


# send chatgpt request
def send_request(question_text,client):

  response = client.chat.completions.create(
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
  print ("*********chatgpt says:" + response.choices[0].message.content +"\n")
  return response.choices[0].message.content



@app.route('/', methods=['GET', 'POST'])
def main_index():
    #return render_template('index.html')
    user_input = ""
    gpt_output = ""
    if request.method=='POST':
        # user_input = request.form.get('asked')
        # gpt_output = send_request(user_input, client)
        # print(f"user has typed: {user_input}")
        file = request.files['audio']
        file.save("uploads/my_sound.wav")
        user_input=audio_to_text()
        gpt_output=send_request(user_input,client)
        gpt_voice = text_to_audio(gpt_output)

    if request.method=='GET':
        user_input = "GET1"
        gpt_output = "GET2"
    return render_template('index.html', user_input=user_input, gpt_output = gpt_output)

# audio to text function using openai tools
def audio_to_text():
    audio_file = open("uploads/my_sound.wav", "rb")
    transcription = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
        response_format="text",
        language="de"
    )
    print("---------ehsan says: " + transcription)
    return transcription

# text to audio function using openai tools
def text_to_audio(text):
    speech_file_path = "uploads/chatgpt_sound.mp3"
    response_voice = openai.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=text
    )
    response_voice.stream_to_file(speech_file_path)
    # return speech_file_path

@app.route('/uploads/chatgpt_sound.mp3')
def serve_audio(filename="chatgpt_sound.mp3"):
    return send_from_directory('uploads', filename)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)

