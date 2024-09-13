const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const photo = document.getElementById('photo');
const fileInput = document.getElementById('file-input');
const captureButton = document.getElementById('capture');

navigator.mediaDevices.getUserMedia({ video: true })
.then(stream => {
    video.srcObject = stream;
    video.play();
})
.catch(err => {
    console.error("Error accessing webcam: " + err);
});

// Capture the photo
captureButton.addEventListener('click', function() {
    const context = canvas.getContext('2d');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    context.drawImage(video, 0, 0, canvas.width, canvas.height);

    // Convert canvas to data URL and show it in img element
    const dataURL = canvas.toDataURL('image/png');
    photo.src = dataURL;
    photo.style.display = 'block';

    // Convert the data URL to a file and set it to the input element
    const file = dataURLToFile(dataURL, 'captured_photo.png');
    const dataTransfer = new DataTransfer();
    dataTransfer.items.add(file);
    fileInput.files = dataTransfer.files;
});

    // Handle form submission
    uploadForm.addEventListener('submit', function(event) {
        if (fileInput.files.length === 0) {
            event.preventDefault();  // Prevent form submission if no photo is captured
            alert('Please capture a photo before uploading.');
        }
    });

// Helper function to convert data URL to file
function dataURLToFile(dataUrl, fileName) {
    const arr = dataUrl.split(',');
    const mime = arr[0].match(/:(.*?);/)[1];
    const bstr = atob(arr[1]);
    let n = bstr.length;
    const u8arr = new Uint8Array(n);
    while (n--) {
        u8arr[n] = bstr.charCodeAt(n);
    }
    return new File([u8arr], fileName, { type: mime });
}