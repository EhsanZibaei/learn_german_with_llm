let mediaRecorder, audioContext, analyser, stream;
let isListening = false, isProcessing = false;
let silenceTimer = null, animationFrameId = null;
let audioChunks = [];

const SILENCE_THRESHOLD = 0.15;
const SPEECH_START_THRESHOLD = 0.4;
const SILENCE_DURATION = 2000;

const toggleBtn = document.getElementById('toggleBtn');
const statusIndicator = document.getElementById('statusIndicator');
const chatContainer = document.getElementById('chatContainer');
const emptyState = document.getElementById('emptyState');
const selectedStyleInput = document.getElementById('selectedStyle');
const selectedModeInput = document.getElementById('selectedMode');

// Status messages in Persian
const status = {
    clickToStart: 'برای شروع کلیک کنید',
    waiting: '🎤 منتظر صحبت شما...',
    recording: '🗣️ در حال ضبط...',
    silenceDetected: '⏳ در حال گوش دادن',
    processing: '📤 در حال پردازش...',
    sending: '📤 ارسال به سرور...',
    waitingAI: '🤖 منتظر پاسخ...',
    playing: '🔊 پخش پاسخ...',
    error: '❌ خطا - دوباره تلاش کنید',
    micDenied: 'دسترسی به میکروفون رد شد'
};

// Style button handlers
document.querySelectorAll('.style-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.style-btn').forEach(b => b.classList.remove('selected'));
        btn.classList.add('selected');
        selectedStyleInput.value = btn.dataset.style;
    });
});

// Mode button handlers
document.querySelectorAll('.mode-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.mode-btn').forEach(b => b.classList.remove('selected'));
        btn.classList.add('selected');
        selectedModeInput.value = btn.dataset.mode;
    });
});

toggleBtn.addEventListener('click', async () => {
    if (!isListening) await startListening();
    else stopListening();
});

async function startListening() {
    try {
        stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        audioContext = new AudioContext();
        analyser = audioContext.createAnalyser();
        const source = audioContext.createMediaStreamSource(stream);
        source.connect(analyser);
        analyser.fftSize = 512;
        analyser.smoothingTimeConstant = 0.8;
        
        isListening = true;
        isProcessing = false;
        toggleBtn.textContent = '🔴 توقف';
        toggleBtn.classList.add('active');
        statusIndicator.textContent = status.waiting;
        
        detectSpeechAndSilence();
    } catch (err) {
        console.error('Mic error:', err);
        statusIndicator.textContent = status.micDenied;
    }
}

function stopListening() {
    isListening = false;
    isProcessing = false;
    toggleBtn.textContent = '🎤 شروع';
    toggleBtn.classList.remove('active');
    statusIndicator.textContent = status.clickToStart;
    
    if (animationFrameId) cancelAnimationFrame(animationFrameId);
    if (silenceTimer) clearTimeout(silenceTimer);
    if (mediaRecorder?.state !== 'inactive') mediaRecorder?.stop();
    stream?.getTracks().forEach(t => t.stop());
    if (audioContext?.state !== 'closed') audioContext?.close();
}

function startRecording() {
    audioChunks = [];
    mediaRecorder = new MediaRecorder(stream);
    mediaRecorder.start();
    mediaRecorder.ondataavailable = e => { if (e.data.size > 0) audioChunks.push(e.data); };
    mediaRecorder.onstop = async () => {
        if (audioChunks.length > 0 && isListening && !isProcessing) {
            isProcessing = true;
            await sendAudioToServer();
        }
    };
}

function getAudioLevel() {
    const data = new Uint8Array(analyser.frequencyBinCount);
    analyser.getByteFrequencyData(data);
    let sum = 0;
    for (let i = 0; i < data.length; i++) sum += (data[i] / 255) ** 2;
    return Math.sqrt(sum / data.length);
}

function detectSpeechAndSilence() {
    let isRecording = false, speechDetected = false;
    
    function check() {
        if (!isListening) return;
        if (isProcessing) { animationFrameId = requestAnimationFrame(check); return; }
        
        const level = getAudioLevel();
        
        if (!isRecording) {
            if (level > SPEECH_START_THRESHOLD) {
                isRecording = true;
                speechDetected = true;
                startRecording();
                statusIndicator.textContent = status.recording;
            }
        } else {
            if (level > SILENCE_THRESHOLD) {
                speechDetected = true;
                if (silenceTimer) { clearTimeout(silenceTimer); silenceTimer = null; }
            } else if (speechDetected && !silenceTimer) {
                statusIndicator.textContent = status.silenceDetected;
                silenceTimer = setTimeout(() => {
                    if (isListening && isRecording && !isProcessing) {
                        statusIndicator.textContent = status.processing;
                        isRecording = false;
                        speechDetected = false;
                        mediaRecorder.stop();
                    }
                    silenceTimer = null;
                }, SILENCE_DURATION);
            }
        }
        animationFrameId = requestAnimationFrame(check);
    }
    check();
}

function addMessage(text, isUser) {
    if (emptyState) emptyState.remove();
    const msg = document.createElement('div');
    msg.className = `message ${isUser ? 'user-message' : 'ai-message'}`;
    msg.innerHTML = `<div class="message-label">${isUser ? 'You' : 'AI'}</div>${text}`;
    chatContainer.appendChild(msg);
    // Always force scroll to bottom after adding message
    setTimeout(() => {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }, 50);
}

async function sendAudioToServer() {
    statusIndicator.textContent = status.sending;
    
    const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
    const audioFile = new File([audioBlob], 'recording.wav', { type: 'audio/wav' });
    const formData = new FormData();
    formData.append('audio', audioFile);
    formData.append('styleType', selectedStyleInput.value);
    formData.append('respondMethod', selectedModeInput.value);
    
    try {
        statusIndicator.textContent = status.waitingAI;
        const response = await fetch('/', { method: 'POST', body: formData });
        
        if (response.ok) {
            const data = await response.json();
            if (data.user_input) addMessage(data.user_input, true);
            if (data.gpt_output) addMessage(data.gpt_output, false);
            await playResponseAudio();
        } else throw new Error('Server error');
    } catch (err) {
        console.error('Error:', err);
        statusIndicator.textContent = status.error;
        isProcessing = false;
    }
}

async function playResponseAudio() {
    try {
        statusIndicator.textContent = status.playing;
        const response = await fetch('uploads/chatgpt_sound.mp3?t=' + Date.now());
        if (!response.ok) throw new Error('Audio fetch failed');
        
        const audioBlob = await response.blob();
        const audioUrl = URL.createObjectURL(audioBlob);
        const audio = new Audio(audioUrl);
        
        await audio.play();
        await new Promise(resolve => { audio.onended = resolve; });
        URL.revokeObjectURL(audioUrl);
        
        await new Promise(r => setTimeout(r, 500));
        if (isListening) {
            isProcessing = false;
            statusIndicator.textContent = status.waiting;
        }
    } catch (err) {
        console.error('Audio error:', err);
        if (isListening) {
            isProcessing = false;
            statusIndicator.textContent = status.waiting;
        }
    }
}