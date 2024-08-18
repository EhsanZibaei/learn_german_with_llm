from flask import Flask, render_template_string, render_template
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
        print("wow")
        file = request.files['audio']
        file.save("uploads/my_sound.wav")
        user_input=audio_to_text()


    if request.method=='GET':
        user_input = "GET1"
        gpt_output = "GET2"
    return render_template('index.html', user_input=user_input, gpt_output = gpt_output)

def audio_to_text():
    audio_file = open("uploads/my_sound.wav", "rb")
    transcription = openai.Audio.transcribe(
        model="whisper-1",
        file=audio_file,
        response_format="text",
        language="de"
    )
    print("---------ehsan says: " + transcription['text'])
    return transcription['text']

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)

