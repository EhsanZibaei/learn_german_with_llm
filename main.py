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
def send_request(question_text, client, system_content, temperature=0.1, max_tokens=70, top_p=1):

  response = client.chat.completions.create(
    model="gpt-4",
    messages=[
      {
        "role": "system",
        "content": system_content
      },
      {
        "role": "user",
        "content": "das ist mein satz: " + question_text
      }
    ],
    temperature=temperature,
    max_tokens=max_tokens,
    top_p=top_p
  )
  #print ("*********chatgpt says:" + response.choices[0].message.content +"\n")
  return response.choices[0].message.content

@app.route('/', methods=['GET', 'POST'])
def choose_task():
   return render_template('start.html')

# endpoint for correcting and proceeding
@app.route('/correcting_proceeding', methods=['GET', 'POST'])
def correct_proceed():
    #return render_template('index.html')
    user_input = ""
    gpt_output = ""
    if request.method=='GET':
        user_input = "GET1"
        gpt_output = "GET2"
    if request.method=='POST':
        if request.form:
          user_input = request.form.get('asked')
          system_content = "erts umformuliere mein satz auf mutterschprachlier deuscth form. dann die gespräsch fortführen."
          gpt_output = send_request(user_input, client, system_content)
          print(f"user has typed: {user_input}")
        if request.files:
          file = request.files['audio']
          file.save("/tmp/my_sound.wav")
          
          user_input=audio_to_text()
          system_content = "erts umformuliere mein satz auf mutterschprachlier deuscth form. dann die gespräsch fortführen."
          gpt_output = send_request(user_input, client, system_content)
          text_to_audio(gpt_output)
    return render_template('index.html', user_input=user_input, gpt_output = gpt_output)

#endpoint for only correcting
@app.route('/correcting', methods=['GET', 'POST'])
def correct():
    user_input = ""
    gpt_output = ""
    if request.method=='GET':
        user_input = "GET1"
        gpt_output = "GET2"
    if request.method=='POST':
        if request.form:
          user_input = request.form.get('asked')
          system_content = "nur umformuliere mein satz auf mutterschprachlier und umgangssprachlicher deuscth form"
          gpt_output = send_request(user_input, client, system_content)
          print(f"user has typed: {user_input}")
        if request.files:
          file = request.files['audio']
          file.save("/tmp/my_sound.wav")
          
          user_input=audio_to_text()
          system_content = "nur umformuliere mein satz auf umgangssprachlicher deuscth form"
          gpt_output = send_request(user_input, client, system_content)
          text_to_audio(gpt_output)
    return render_template('index.html', user_input=user_input, gpt_output = gpt_output)

# audio to text function using openai tools
def audio_to_text():
    audio_file = open("/tmp/my_sound.wav", "rb")
    transcription = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
        response_format="text",
        language="de"
    )
    # print("---------ehsan says: " + transcription)
    return transcription

# text to audio function using openai tools
def text_to_audio(text):
    speech_file_path = "/tmp/chatgpt_sound.mp3"
    with client.audio.speech.with_streaming_response.create(
        model="tts-1",
        voice="alloy",
        input=text,
    ) as response:
        response.stream_to_file(speech_file_path)

@app.route('/uploads/chatgpt_sound.mp3')
def serve_audio(filename="chatgpt_sound.mp3"):
    return send_from_directory('/tmp', filename)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)

