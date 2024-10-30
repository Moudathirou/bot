"""from flask import Flask, render_template, request, jsonify,send_from_directory
from flask_socketio import SocketIO, emit
import os
from dotenv import load_dotenv
from rag import RAGModule

from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Permet les requêtes cross-origin
app.config['SECRET_KEY'] = 'votre_clé_secrète'
socketio = SocketIO(app, cors_allowed_origins="*")
load_dotenv()

# Initialize RAG module
rag_module = RAGModule()
chat_history = []  # Store chat history

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('send_message')
def handle_message(data):
    global chat_history
    user_message = data['message']
    
    # Use the RAG module to get response
    response = rag_module.get_response(user_message, chat_history)
    
    # Update chat history
    chat_history.append(("human", user_message))
    chat_history.append(("assistant", response["answer"]))
    
    emit('bot_response', {'message': response["answer"]})

if __name__ == '__main__':
    socketio.run(app, debug=True)"""


from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
import os
from dotenv import load_dotenv
from rag import RAGModule
from flask_cors import CORS

app = Flask(__name__)



CORS(app)
app.config['SECRET_KEY'] = 'votre_clé_secrète'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
load_dotenv()

# Initialize RAG module
rag_module = RAGModule()
chat_history = []  # Store chat history

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('send_message')
def handle_message(data):
    global chat_history
    user_message = data['message']
    
    # Use the RAG module to get response
    response = rag_module.get_response(user_message, chat_history)
    
    # Update chat history
    chat_history.append(("human", user_message))
    chat_history.append(("assistant", response["answer"]))
    
    emit('bot_response', {'message': response["answer"]})


@app.after_request
def add_header(response):
    response.headers['X-Frame-Options'] = 'ALLOWALL'
    return response


if __name__ == '__main__':
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)