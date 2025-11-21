from flask import Flask, render_template, send_from_directory, request, jsonify
import os
from env.openai_key import API_KEY
import openai

app = Flask(__name__, static_folder='static')
os.environ["OPENAI_API_KEY"] = API_KEY
openai.api_key = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI()

STYLES = {
    "colloquial": "colloquial",
    "native": "native-like",
    "business": "business-professional",
    "minimal": "correct"
}

PROMPTS = {
    "monologue": "Only rephrase my sentence in very {style} English.",
    "dialogue": "Rephrase my sentence in very {style} English. Then continue the conversation."
}

MINIMAL_PROMPTS = {
    "monologue": "Correct my sentence with minimal changes. Only fix what is grammatically or linguistically wrong, keep my style and word choices as much as possible.",
    "dialogue": "Correct my sentence with minimal changes. Only fix what is grammatically or linguistically wrong. Then continue the conversation."
}

def send_request(question, system_content):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_content},
            {"role": "user", "content": " " + question}
        ],
        temperature=0.1,
        max_tokens=150,
        top_p=1
    )
    return response.choices[0].message.content

def audio_to_text():
    with open("/tmp/my_sound.wav", "rb") as f:
        return client.audio.transcriptions.create(
            model="whisper-1", file=f, response_format="text", language="en"
        )

def text_to_audio(text):
    with client.audio.speech.with_streaming_response.create(
        model="tts-1", voice="alloy", input=text
    ) as response:
        response.stream_to_file("/tmp/chatgpt_sound.mp3")

@app.route('/', methods=['GET'])
def serve_index():
    return render_template('index.html')

@app.route('/', methods=['POST'])
def process_audio():
    user_input = ""
    gpt_output = ""
    
    style_type = request.form.get('styleType', 'minimal')
    respond_type = request.form.get('respondMethod', 'monologue')
    
    if 'audio' in request.files:
        request.files['audio'].save("/tmp/my_sound.wav")
        user_input = audio_to_text()
        
        if respond_type != 'answer':
            if style_type == 'minimal':
                system_content = MINIMAL_PROMPTS.get(respond_type, MINIMAL_PROMPTS["monologue"])
            else:
                style = STYLES.get(style_type, STYLES["native"])
                system_content = PROMPTS.get(respond_type, PROMPTS["monologue"]).format(style=style)
        else:
            system_content = "If the user asked a question answer in English. If the tone of the user implies interrogation, then answer it without asking a question. Say only one sentence. if the user's sentence was not interrogative, either ask a question or say something in the same topic of users sentence. Keep the sentence in the A1 english level."
        
        gpt_output = send_request(user_input, system_content)
        text_to_audio(gpt_output)
    
    return jsonify({"user_input": user_input, "gpt_output": gpt_output})

@app.route('/uploads/chatgpt_sound.mp3')
def serve_audio():
    return send_from_directory('/tmp', 'chatgpt_sound.mp3')

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)