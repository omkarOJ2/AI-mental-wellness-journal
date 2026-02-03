// FIXED Voice Input - No Repetition + Multi-Language Support
let recognition = null;
let isRecording = false;

// Check if browser supports speech recognition
if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();

    recognition.continuous = false; // Changed to false to prevent repetition
    recognition.interimResults = false; // Changed to false for cleaner results
    recognition.lang = 'en-US'; // Default language

    recognition.onstart = () => {
        isRecording = true;
        document.getElementById('voiceInputBtn').classList.add('recording');
        console.log('Voice recognition started');
    };

    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;

        // Simply append the new transcript to existing content
        const currentValue = document.getElementById('journalContent').value;
        const newValue = currentValue + (currentValue ? ' ' : '') + transcript;

        document.getElementById('journalContent').value = newValue;

        // Update character counter
        const characterCounter = document.getElementById('characterCounter');
        characterCounter.textContent = `${newValue.length} character${newValue.length !== 1 ? 's' : ''}`;
    };

    recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        isRecording = false;
        document.getElementById('voiceInputBtn').classList.remove('recording');

        if (event.error === 'not-allowed') {
            showNotification('Microphone access denied. Please allow microphone access.', 'error');
        } else if (event.error === 'no-speech') {
            showNotification('No speech detected. Please try again.', 'error');
        } else {
            showNotification('Voice recognition error. Please try again.', 'error');
        }
    };

    recognition.onend = () => {
        isRecording = false;
        document.getElementById('voiceInputBtn').classList.remove('recording');
        console.log('Voice recognition ended');
    };
}

// Voice input button click handler
document.getElementById('voiceInputBtn').addEventListener('click', () => {
    if (!recognition) {
        showNotification('Voice input is not supported in your browser. Please use Chrome, Edge, or Safari.', 'error');
        return;
    }

    // Get selected language
    const langSelect = document.getElementById('voiceLangSelect');
    if (langSelect) {
        recognition.lang = langSelect.value;
    }

    if (isRecording) {
        recognition.stop();
    } else {
        recognition.start();
    }
});
