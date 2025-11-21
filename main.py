from flask import Flask, render_template, send_from_directory, request
import os
from env.openai_key import API_KEY
import openai
from openai import OpenAI

app = Flask(__name__, static_folder='static')
os.environ["OPENAI_API_KEY"] = API_KEY
OpenAI.api_key = os.getenv("OPENAI_API_KEY")
MODEL_NAME = "gpt-4o"
SEED = 42
client = openai.OpenAI()

# Language configurations
LANGUAGE_CONFIG = {
    "german": {
        "code": "de",
        "whisper_lang": "de",
        "prompts": {
            "monologue": "nur Formuliere meinen Satz auf sehr {style} deutsch form.",
            "dialogue": "Formuliere meinen Satz auf sehr {style} deutsch form. Danach fahre bitte mit dem Gespräch fort.",
        },
        "styles": {
            "colloquial": "umgangssprachlich",
            "native": "muttersprachlich",
            "business": "geschäftssprachlich",
            "minimal": "korrekt"
        },
        "minimal_prompt": {
            "monologue": "Korrigiere meinen Satz mit so wenigen Änderungen wie möglich. Ändere nur was grammatikalisch oder sprachlich falsch ist, behalte meinen Stil und meine Wortwahl bei.",
            "dialogue": "Korrigiere meinen Satz mit so wenigen Änderungen wie möglich. Ändere nur was grammatikalisch oder sprachlich falsch ist. Danach fahre bitte mit dem Gespräch fort."
        },
        "prefix": " "
    },
    "english": {
        "code": "en",
        "whisper_lang": "en",
        "prompts": {
            "monologue": "Only rephrase my sentence in very {style} English.",
            "dialogue": "Rephrase my sentence in very {style} English. Then continue the conversation.",
        },
        "styles": {
            "colloquial": "colloquial",
            "native": "native-like",
            "business": "business-professional",
            "minimal": "correct"
        },
        "minimal_prompt": {
            "monologue": "Correct my sentence with minimal changes. Only fix what is grammatically or linguistically wrong, keep my style and word choices as much as possible.",
            "dialogue": "Correct my sentence with minimal changes. Only fix what is grammatically or linguistically wrong. Then continue the conversation."
        },
        "prefix": " "
    },
    "farsi": {
        "code": "fa",
        "whisper_lang": "fa",
        "prompts": {
            "monologue": "فقط جمله من را به فارسی {style} بازنویسی کن.",
            "dialogue": "جمله من را به فارسی {style} بازنویسی کن. سپس مکالمه را ادامه بده.",
        },
        "styles": {
            "colloquial": "محاوره‌ای",
            "native": "روان و طبیعی",
            "business": "رسمی و اداری",
            "minimal": "صحیح"
        },
        "minimal_prompt": {
            "monologue": "جمله من را با کمترین تغییرات ممکن اصلاح کن. فقط اشتباهات دستوری یا زبانی را تصحیح کن و سبک و انتخاب کلمات من را حفظ کن.",
            "dialogue": "جمله من را با کمترین تغییرات ممکن اصلاح کن. فقط اشتباهات دستوری یا زبانی را تصحیح کن. سپس مکالمه را ادامه بده."
        },
        "prefix": ""
    }
}

def send_request(question_text, client, system_content, temperature=0.1, max_tokens=70, top_p=1):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_content},
            {"role": "user", "content": question_text}
        ],
        temperature=temperature,
        max_tokens=max_tokens,
        top_p=top_p
    )
    return response.choices[0].message.content

@app.route('/', methods=['GET'])
def serve_index():
    return render_template('index.html', user_input="", gpt_output="")

@app.route('/', methods=['POST'])
def update_index():
    user_input = ""
    gpt_output = ""
    
    # Get form parameters
    temperature = request.form.get('temperature', 0.1, type=float)
    max_tokens = request.form.get('max_tokens', 70, type=int)
    top_p = request.form.get('top_p', 1.0, type=float)
    
    # Get language and style selections
    selected_language = request.form.get('selectedLanguage', 'german', type=str).lower()
    style_type = request.form.get('styleType', 'native', type=str).lower()
    respond_type = request.form.get('respondMethod', 'monologue', type=str)
    
    # Get language config (default to german if invalid)
    lang_config = LANGUAGE_CONFIG.get(selected_language, LANGUAGE_CONFIG["german"])
    
    if request.files and 'audio' in request.files:
        file = request.files['audio']
        file.save("/tmp/my_sound.wav")
        
        # Transcribe audio in the selected language
        user_input = audio_to_text(lang_config["whisper_lang"])
        
        if respond_type != 'answer':
            # Get the style in the target language
            style = lang_config["styles"].get(style_type, lang_config["styles"]["native"])
            
            # Check if minimal style (closest correct form)
            if style_type == 'minimal' and 'minimal_prompt' in lang_config:
                if respond_type == 'monologue':
                    system_content = lang_config["minimal_prompt"]["monologue"]
                else:  # dialogue
                    system_content = lang_config["minimal_prompt"]["dialogue"]
            elif respond_type == 'monologue':
                system_content = lang_config["prompts"]["monologue"].format(style=style)
            else:  # dialogue
                system_content = lang_config["prompts"]["dialogue"].format(style=style)
            
            question = lang_config["prefix"] + user_input
        else:
            # Just answer the question
            system_content = f"Answer in {selected_language}. Be helpful and conversational."
            question = user_input
        
        gpt_output = send_request(question, client, system_content, temperature, max_tokens, top_p)
        text_to_audio(gpt_output)
    
    return render_template('index.html', user_input=user_input, gpt_output=gpt_output)

def audio_to_text(language="de"):
    audio_file = open("/tmp/my_sound.wav", "rb")
    transcription = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
        response_format="text",
        language=language
    )
    return transcription

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
