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

# endpoint for correcting and proceeding
@app.route('/', methods=['GET'])
def serve_index():
    #return render_template('index.html')
    user_input = ""
    gpt_output = ""
    return render_template('index.html', user_input=user_input, gpt_output = gpt_output)

@app.route('/', methods=['POST'])
def update_index():
    #return render_template('index.html')
    user_input = ""
    gpt_output = ""
    
    if request.form:
      # user_input = request.form.get('asked')
      # system_content = "erts umformuliere mein satz auf mutterschprachlier deuscth form. dann die gespräsch fortführen."
      temperature = request.form.get('temperature', type=float)
      max_tokens = request.form.get('max_tokens', type=int)
      top_p = request.form.get('top_p', type=float)
      # gpt_output = send_request(user_input, client, system_content, temperature, max_tokens, top_p)
      languageType = request.form.get('language', type=str)
      respondType = request.form.get('respondMethod', type=str)
      print(f"user has typed: {user_input}")

    if request.files:
      file = request.files['audio']
      file.save("/tmp/my_sound.wav")
      
      user_input=audio_to_text()
      if respondType != 'answer':
        if respondType=='monologue':
          system_content = f"nur Formuliere meinen Satz auf sehr {languageType} deuscth form."
          

        elif respondType == 'dialogue':
          system_content = f"Formuliere meinen Satz auf sehr {languageType} deuscth form. Danach fahre bitte mit dem Gespräch fort"
      else:
          system_content = user_input

      gpt_output = send_request(user_input, client, system_content, temperature, max_tokens, top_p)
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

