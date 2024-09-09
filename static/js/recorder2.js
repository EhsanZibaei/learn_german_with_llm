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
    mediaRecorder.ondataavailable = (event) => {
        audioChunks.push(event.data);
    };

    mediaRecorder.onstop = async () => {

        const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
        const audioFile = new File([audioBlob], 'recording.wav', { type: 'audio/wav' });
        const dataTransfer = new DataTransfer();
        dataTransfer.items.add(audioFile);
        audioFileInput.files = dataTransfer.files;
        uploadBtn.disabled = false;
        const formData = new FormData();
        formData.append('audio', audioFile);

        // update the user chosen setting
        formData.append('temperature', document.getElementById('creativity').value);
        formData.append('max_tokens', document.getElementById('length').value);
        formData.append('top_p', document.getElementById('predictability').value);

        // document.getElementById("uploadForm").submit()

        const response = await fetch('/', {
            method: 'POST',
            body: formData,
        });
        if (response.ok) {
            // Trigger the click only after the POST request has returned successfully
            const data = await response.text();
            const parser = new DOMParser();
            const doc = parser.parseFromString(data, 'text/html'); // Parse the HTML string
            // const pElement = doc.querySelector('p'); 
            console.log('Content of <p> element:', doc.getElementById("user_updated")); // Access the content of the <p> element
            document.getElementById("user_updated").innerHTML = doc.getElementById("user_updated").innerHTML;
            document.getElementById("gpt_updated").innerHTML = doc.getElementById("gpt_updated").innerHTML;

            document.getElementById("fetchAudioBtn").click();
        } else {
            console.error('Upload failed', response.statusText);
        }

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

document.getElementById('fetchAudioBtn').addEventListener('click', async () => {
    try {
        const response = await fetch('uploads/chatgpt_sound.mp3'); // Update the filename as needed
        if (!response.ok) throw new Error('Network response was not ok.');
        
        const audioBlob = await response.blob();
        const audioUrl = URL.createObjectURL(audioBlob);
        
        const audioPlayer = document.getElementById('audioPlayer');
        audioPlayer.src = audioUrl;
        audioPlayer.play();
    } catch (error) {
        console.error('Error fetching the audio file:', error);
    }
});