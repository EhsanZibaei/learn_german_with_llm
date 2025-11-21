let mediaRecorder;
let audioContext;
let analyser;
let stream;
let isListening = false;
let isProcessing = false; // New flag to block listening during processing/playback
let silenceTimer = null;
let audioChunks = [];
let animationFrameId = null;

// Much higher threshold - requires loud, clear speech
const SILENCE_THRESHOLD = 0.15;
// Minimum volume to START recording (even higher)
const SPEECH_START_THRESHOLD = 0.4;
const SILENCE_DURATION = 2000; // 2 seconds

const toggleBtn = document.getElementById('toggleBtn');
const statusIndicator = document.getElementById('statusIndicator');
const audioPlayer = document.getElementById('audioPlayer');

// Language selection handling
const langBtns = document.querySelectorAll('.lang-btn');
const selectedLanguageInput = document.getElementById('selectedLanguage');

const styleLabels = {
    german: { colloquial: 'Umgangssprachlich', native: 'Muttersprachlich', business: 'Geschäftssprachlich', minimal: 'Minimale Korrektur' },
    english: { colloquial: 'Colloquial', native: 'Native', business: 'Business', minimal: 'Closest Correct Form' },
    farsi: { colloquial: 'محاوره‌ای', native: 'روان', business: 'رسمی', minimal: 'نزدیک‌ترین شکل صحیح' }
};

langBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        langBtns.forEach(b => b.classList.remove('selected'));
        btn.classList.add('selected');
        const lang = btn.dataset.lang;
        selectedLanguageInput.value = lang;
        
        // Update style labels based on language
        document.getElementById('styleLabel1').textContent = styleLabels[lang].colloquial;
        document.getElementById('styleLabel2').textContent = styleLabels[lang].native;
        document.getElementById('styleLabel3').textContent = styleLabels[lang].business;
        document.getElementById('styleLabel4').textContent = styleLabels[lang].minimal;
    });
});

toggleBtn.addEventListener('click', async () => {
    if (!isListening) {
        await startListening();
    } else {
        stopListening();
    }
});

async function startListening() {
    try {
        stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        audioContext = new AudioContext();
        analyser = audioContext.createAnalyser();
        const source = audioContext.createMediaStreamSource(stream);
        source.connect(analyser);
        analyser.fftSize = 512;
        analyser.smoothingTimeConstant = 0.8; // Smooth out noise spikes
        
        isListening = true;
        isProcessing = false;
        toggleBtn.textContent = '🔴 Stop Chat';
        toggleBtn.classList.add('active');
        statusIndicator.textContent = '🎤 Waiting for you to speak loudly...';
        
        detectSpeechAndSilence();
    } catch (err) {
        console.error('Error accessing microphone:', err);
        statusIndicator.textContent = 'Microphone access denied';
    }
}

function stopListening() {
    isListening = false;
    isProcessing = false;
    toggleBtn.textContent = '🎤 Start Chat';
    toggleBtn.classList.remove('active');
    statusIndicator.textContent = 'Click to start';
    
    if (animationFrameId) {
        cancelAnimationFrame(animationFrameId);
        animationFrameId = null;
    }
    if (silenceTimer) {
        clearTimeout(silenceTimer);
        silenceTimer = null;
    }
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
    }
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
    }
    if (audioContext && audioContext.state !== 'closed') {
        audioContext.close();
    }
}

function startRecording() {
    audioChunks = [];
    mediaRecorder = new MediaRecorder(stream);
    mediaRecorder.start();
    
    mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunks.push(e.data);
    };
    
    mediaRecorder.onstop = async () => {
        if (audioChunks.length > 0 && isListening && !isProcessing) {
            isProcessing = true; // Block any further listening
            await sendAudioToServer();
        }
    };
}

function getAudioLevel() {
    const dataArray = new Uint8Array(analyser.frequencyBinCount);
    analyser.getByteFrequencyData(dataArray);
    // Use RMS for more accurate level detection
    let sum = 0;
    for (let i = 0; i < dataArray.length; i++) {
        const normalized = dataArray[i] / 255;
        sum += normalized * normalized;
    }
    return Math.sqrt(sum / dataArray.length);
}

function detectSpeechAndSilence() {
    let isRecording = false;
    let speechDetected = false;
    
    function checkAudio() {
        if (!isListening) return;
        
        // Skip all audio detection while processing or playing response
        if (isProcessing) {
            animationFrameId = requestAnimationFrame(checkAudio);
            return;
        }
        
        const level = getAudioLevel();
        
        // State: Waiting for speech to start
        if (!isRecording) {
            if (level > SPEECH_START_THRESHOLD) {
                // Speech detected! Start recording
                isRecording = true;
                speechDetected = true;
                startRecording();
                statusIndicator.textContent = '🗣️ Recording... Speak clearly!';
                console.log('Speech started, recording...');
            }
        } 
        // State: Currently recording
        else {
            if (level > SILENCE_THRESHOLD) {
                // Still speaking
                speechDetected = true;
                statusIndicator.textContent = '🗣️ Recording... (level: ' + level.toFixed(2) + ')';
                if (silenceTimer) {
                    clearTimeout(silenceTimer);
                    silenceTimer = null;
                }
            } else if (speechDetected && !silenceTimer) {
                // Silence started after speech
                statusIndicator.textContent = '⏳ Silence detected, waiting 2s...';
                silenceTimer = setTimeout(() => {
                    if (isListening && isRecording && !isProcessing) {
                        console.log('2 seconds of silence confirmed, sending...');
                        statusIndicator.textContent = '📤 Processing your request...';
                        isRecording = false;
                        speechDetected = false;
                        mediaRecorder.stop(); // This triggers onstop -> sendAudioToServer
                    }
                    silenceTimer = null;
                }, SILENCE_DURATION);
            }
        }
        
        animationFrameId = requestAnimationFrame(checkAudio);
    }
    
    checkAudio();
}

async function sendAudioToServer() {
    statusIndicator.textContent = '📤 Sending to server...';
    
    const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
    const audioFile = new File([audioBlob], 'recording.wav', { type: 'audio/wav' });
    const formData = new FormData();
    formData.append('audio', audioFile);
    
    formData.append('temperature', document.getElementById('creativity').value);
    formData.append('max_tokens', document.getElementById('length').value);
    formData.append('top_p', document.getElementById('predictability').value);
    
    // Selected language (german, english, farsi)
    formData.append('selectedLanguage', document.getElementById('selectedLanguage').value);
    
    // Style type (colloquial, native, business)
    const styleRadios = document.querySelectorAll('input[name="styleType"]');
    styleRadios.forEach(radio => {
        if (radio.checked) formData.append('styleType', radio.value);
    });
    
    // Response method (monologue, dialogue, answer)
    const respondTypes = document.querySelectorAll('#monologueDialogue input[type="radio"]');
    respondTypes.forEach(r => {
        if (r.checked) formData.append('respondMethod', r.value);
    });
    
    try {
        statusIndicator.textContent = '🤖 Waiting for AI response...';
        const response = await fetch('/', { method: 'POST', body: formData });
        
        if (response.ok) {
            const data = await response.text();
            const parser = new DOMParser();
            const doc = parser.parseFromString(data, 'text/html');
            document.getElementById("user_updated").innerHTML = doc.getElementById("user_updated").innerHTML;
            document.getElementById("gpt_updated").innerHTML = doc.getElementById("gpt_updated").innerHTML;
            
            await playResponseAudio();
        } else {
            throw new Error('Server error');
        }
    } catch (err) {
        console.error('Upload failed:', err);
        statusIndicator.textContent = '❌ Error - Click to try again';
        isProcessing = false;
    }
}

async function playResponseAudio() {
    try {
        statusIndicator.textContent = '🔊 Playing response...';
        
        const response = await fetch('uploads/chatgpt_sound.mp3?t=' + Date.now()); // Cache bust
        if (!response.ok) throw new Error('Failed to fetch audio');
        
        const audioBlob = await response.blob();
        const audioUrl = URL.createObjectURL(audioBlob);
        audioPlayer.src = audioUrl;
        
        // Wait for audio to fully load
        await new Promise((resolve, reject) => {
            audioPlayer.oncanplaythrough = resolve;
            audioPlayer.onerror = reject;
        });
        
        await audioPlayer.play();
        
        // Wait for audio to finish playing completely
        await new Promise((resolve) => {
            audioPlayer.onended = () => {
                URL.revokeObjectURL(audioUrl);
                resolve();
            };
        });
        
        // Small delay after audio ends before listening again
        await new Promise(resolve => setTimeout(resolve, 500));
        
        // Now ready to listen again
        if (isListening) {
            isProcessing = false;
            statusIndicator.textContent = '🎤 Waiting for you to speak loudly...';
        }
        
    } catch (err) {
        console.error('Error playing audio:', err);
        if (isListening) {
            isProcessing = false;
            statusIndicator.textContent = '🎤 Waiting for you to speak loudly...';
        }
    }
}