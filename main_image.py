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

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/image', methods=['POST'])
def upload_photo():
    if 'photo' not in request.files:
        return 'No file part'
    
    file = request.files['photo']
    if file.filename == '':
        return 'No selected file'
    
    if file:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)
        return f'File uploaded: {file_path}'
    
@app.route('/image', methods=['GET'])
def serve_text():
    return render_template('start.html')


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)