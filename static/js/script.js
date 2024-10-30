const socket = io();
let mediaRecorder;
let audioChunks = [];
let recognition;

// Initialize speech recognition
if ('webkitSpeechRecognition' in window) {
    recognition = new webkitSpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    
    recognition.onresult = (event) => {
        const result = event.results[event.results.length - 1];
        if (result.isFinal) {
            const transcript = result.item(0).transcript;
            document.getElementById('user-input').value = transcript;
        }
    };
    
    recognition.onend = () => {
        const speakBtn = document.getElementById('speak-btn');
        speakBtn.classList.remove('recording');
        if (document.getElementById('user-input').value) {
            sendMessage();
        }
    };
}

document.getElementById('send-btn').addEventListener('click', sendMessage);
document.getElementById('user-input').addEventListener('keypress', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

document.getElementById('speak-btn').addEventListener('click', toggleSpeechRecognition);

function sendMessage() {
    const userInput = document.getElementById('user-input');
    const message = userInput.value.trim();
    if (message !== '') {
        appendMessage(message, true);
        socket.emit('send_message', { message: message });
        userInput.value = '';
    }
}

function appendMessage(message, isUser = false) {
    const chatMessages = document.getElementById('chat-messages');
    const messageElement = document.createElement('div');
    messageElement.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
    messageElement.textContent = message;
    chatMessages.appendChild(messageElement);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function toggleSpeechRecognition() {
    const speakBtn = document.getElementById('speak-btn');
    
    if (recognition) {
        if (speakBtn.classList.contains('recording')) {
            recognition.stop();
        } else {
            speakBtn.classList.add('recording');
            recognition.start();
        }
    }
}

socket.on('connect', () => {
    console.log('Connected to server');
});

socket.on('disconnect', () => {
    console.log('Disconnected from server');
});

socket.on('bot_response', (data) => {
    appendMessage(data.message, false);
});

socket.on('error', (error) => {
    console.error('Socket.IO Error:', error);
});