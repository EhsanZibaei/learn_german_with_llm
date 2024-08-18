let mediaRecorder;


const startBtn = document.getElementById('startBtn');
const stopBtn = document.getElementById('stopBtn');
const uploadForm = document.getElementById('uploadForm');
const audioFileInput = document.getElementById('audioFile');
const uploadBtn = document.getElementById('uploadBtn');

startBtn.addEventListener('click', async () => {
    let audioChunks = [];
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(stream);
    mediaRecorder.start();
    console.log("i coul dcome here");
    mediaRecorder.ondataavailable = (event) => {
        audioChunks.push(event.data);
    };

    mediaRecorder.onstop = () => {

        const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
        const audioFile = new File([audioBlob], 'recording.wav', { type: 'audio/wav' });
        const dataTransfer = new DataTransfer();
        dataTransfer.items.add(audioFile);
        audioFileInput.files = dataTransfer.files;
        uploadBtn.disabled = false;
    };

    startBtn.disabled = true;
    stopBtn.disabled = false;
});

stopBtn.addEventListener('click', () => {
    mediaRecorder.stop();
    startBtn.disabled = false;
    stopBtn.disabled = true;
});

uploadForm.addEventListener('submit', (event) => {
    if (audioFileInput.files.length === 0) {
        event.preventDefault();
        alert("No audio recorded");
    }
    //window.location.reload();
});
