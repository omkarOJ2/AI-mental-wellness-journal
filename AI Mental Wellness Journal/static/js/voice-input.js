// Voice Input Feature for Mental Wellness Journal
// Uses Web Speech API for voice-to-text transcription

class VoiceInput {
    constructor() {
        this.recognition = null;
        this.isListening = false;
        this.transcript = '';
        this.initRecognition();
    }

    initRecognition() {
        // Check browser support
        if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
            console.error('Speech recognition not supported');
            return;
        }

        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        this.recognition = new SpeechRecognition();

        // Configuration
        this.recognition.continuous = true;
        this.recognition.interimResults = true;
        this.recognition.lang = 'en-US';

        // Event handlers
        this.recognition.onresult = (event) => {
            let interimTranscript = '';
            let finalTranscript = '';

            for (let i = event.resultIndex; i < event.results.length; i++) {
                const transcript = event.results[i][0].transcript;
                if (event.results[i].isFinal) {
                    finalTranscript += transcript + ' ';
                } else {
                    interimTranscript += transcript;
                }
            }

            this.transcript = finalTranscript;
            this.onTranscript(finalTranscript, interimTranscript);
        };

        this.recognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
            this.isListening = false;
            this.onError(event.error);
        };

        this.recognition.onend = () => {
            this.isListening = false;
            this.onEnd();
        };
    }

    start() {
        if (!this.recognition) {
            alert('Voice input is not supported in your browser');
            return;
        }

        if (this.isListening) {
            this.stop();
            return;
        }

        this.transcript = '';
        this.recognition.start();
        this.isListening = true;
        this.onStart();
    }

    stop() {
        if (this.recognition && this.isListening) {
            this.recognition.stop();
            this.isListening = false;
        }
    }

    // Callback functions (to be overridden)
    onTranscript(finalTranscript, interimTranscript) {
        // Override this in implementation
    }

    onStart() {
        // Override this in implementation
    }

    onEnd() {
        // Override this in implementation
    }

    onError(error) {
        // Override this in implementation
    }
}

// Initialize voice input for journal entry
function initVoiceInputForJournal() {
    const voiceInput = new VoiceInput();
    const voiceButton = document.getElementById('voiceInputBtn');
    const journalTextarea = document.getElementById('journalContent');

    if (!voiceButton || !journalTextarea) return;

    // Override callbacks
    voiceInput.onTranscript = (finalTranscript, interimTranscript) => {
        // Append final transcript to textarea
        if (finalTranscript) {
            const currentText = journalTextarea.value;
            journalTextarea.value = currentText + finalTranscript;
        }
    };

    voiceInput.onStart = () => {
        voiceButton.classList.add('recording');
        voiceButton.innerHTML = '<i class="fas fa-stop"></i> Stop Recording';
        voiceButton.style.background = 'linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%)';
    };

    voiceInput.onEnd = () => {
        voiceButton.classList.remove('recording');
        voiceButton.innerHTML = '<i class="fas fa-microphone"></i> Voice Input';
        voiceButton.style.background = '';
    };

    voiceInput.onError = (error) => {
        alert(`Voice input error: ${error}`);
        voiceButton.classList.remove('recording');
        voiceButton.innerHTML = '<i class="fas fa-microphone"></i> Voice Input';
        voiceButton.style.background = '';
    };

    // Button click handler
    voiceButton.addEventListener('click', () => {
        voiceInput.start();
    });
}

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initVoiceInputForJournal);
} else {
    initVoiceInputForJournal();
}
