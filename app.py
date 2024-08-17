from flask import Flask, render_template_string, render_template
from flask import request
import os
from openai import OpenAI
from env.openai_key import API_KEY

app = Flask(__name__)

os.environ["OPENAI_API_KEY"] = API_KEY
OpenAI.api_key = os.getenv("OPENAI_API_KEY")
MODEL_NAME = "gpt-4o"
SEED = 42

client = OpenAI()

@app.route('/', methods=['GET', 'POST'])
def index():
    my_sentence = ""
    if request.method == 'POST':
        my_sentence = request.form['sentence']

    return render_template_string('''
        <!doctype html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Submit a Sentence</title>
        </head>
        <body>
            <h1>Submit a Sentence</h1>
            <form method="POST">
                <label for="sentence">Sentence:</label>
                <input type="text" id="sentence" name="sentence" required>
                <input type="submit" value="Submit">
            </form>
            {% if sentence %}
                <p>You submitted: {{ sentence }}</p>
            {% endif %}
        </body>
        </html>
    ''', sentence=sentence)

def fahrenheit_from(celsius):
    """Convert Celsius to Fahrenheit degrees."""
    try: 
        fahrenheit = float(celsius) * 9 / 5 + 32
        fahrenheit = round(fahrenheit, 3)  # Round to three decimal places
        return str(fahrenheit)
    except ValueError:
        print ("invalid input")

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

# test chatgpt functions one by one
@app.route("/test")
def testing_func():
    new_response = request.args.get("test", "")
    new_response = send_request("bin ich fenster?", client)
    return """<form action="" method="get">
                <input type="text" name="celsius">
                <input type="submit" value="Convert">
              </form> """ + new_response

@app.route('/hello', methods=['GET', 'POST'])
def main_index():
    #return render_template('index.html')
    user_input = ""
    gpt_output = ""
    if request.method=='POST':
        user_input = request.form.get('asked')
        gpt_output = send_request(user_input, client)
        print(f"user has typed: {user_input}")
    if request.method=='GET':
        user_input = "GET1"
        gpt_output = "GET2"
    return render_template('index.html', user_input=user_input, gpt_output = gpt_output)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)

