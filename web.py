"""
SAISA Web Interface
Interface graphique dans le navigateur!
Lance: python web.py
Puis ouvre: http://localhost:7860
"""

import os
import sys
from pathlib import Path

# Configuration
os.environ['AGENT_BACKEND'] = 'ollama'
os.environ['OLLAMA_MODEL'] = 'llama3.2'

import httpx

# ==== CONFIGURATION ====
OLLAMA_URL = "http://127.0.0.1:11434"
MODEL = "llama3.2"
SYSTEM_PROMPT = """Tu es SAISA, un assistant IA intelligent et utiles tes outils si besoin. 
Tu peux rechercher sur le web, créer des fichiers, etc.
Réponds en français de manière claire et concise."""

def chat(message, history=None):
    """Envoie un message à l'IA"""
    client = httpx.Client(timeout=120.0)
    
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    # Ajouter l'historique
    if history:
        for user_msg, bot_msg in history:
            messages.append({"role": "user", "content": user_msg})
            messages.append({"role": "assistant", "content": bot_msg})
    
    messages.append({"role": "user", "content": message})
    
    try:
        response = client.post(
            f"{OLLAMA_URL}/api/chat",
            json={"model": MODEL, "messages": messages, "stream": False}
        )
        
        if response.status_code != 200:
            return f"Erreur: {response.status_code}"
        
        return response.json()['message']['content']
    except Exception as e:
        return f"Erreur: {e}"
    finally:
        client.close()

# ==== INTERFACE WEB avec Flask ====
try:
    from flask import Flask, render_template_string, request, jsonify
    HAS_FLASK = True
except ImportError:
    HAS_FLASK = False
    print("Flask pas installé. pip install flask")

if HAS_FLASK:
    app = Flask(__name__)
    
    HTML_TEMPLATE = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>SAISA - Interface Web</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * { box-sizing: border-box; margin: 0; padding: 0; }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: #1a1a2e;
                color: #eee;
                height: 100vh;
                display: flex;
                flex-direction: column;
            }
            header {
                background: #16213e;
                padding: 15px 20px;
                border-bottom: 1px solid #0f3460;
                display: flex;
                align-items: center;
                gap: 10px;
            }
            header h1 { font-size: 1.5rem; color: #e94560; }
            header .badge {
                background: #0f3460;
                padding: 3px 8px;
                border-radius: 4px;
                font-size: 0.7rem;
            }
            #chat {
                flex: 1;
                overflow-y: auto;
                padding: 20px;
                display: flex;
                flex-direction: column;
                gap: 15px;
            }
            .message {
                max-width: 80%;
                padding: 12px 16px;
                border-radius: 12px;
                line-height: 1.5;
            }
            .message.user {
                align-self: flex-end;
                background: #e94560;
                color: white;
            }
            .message.bot {
                align-self: flex-start;
                background: #16213e;
                border: 1px solid #0f3460;
            }
            .typing {
                color: #888;
                font-style: italic;
            }
            #input-area {
                background: #16213e;
                padding: 15px;
                border-top: 1px solid #0f3460;
                display: flex;
                gap: 10px;
            }
            #input-area input {
                flex: 1;
                padding: 12px 16px;
                border: 1px solid #0f3460;
                border-radius: 8px;
                background: #1a1a2e;
                color: #eee;
                font-size: 1rem;
            }
            #input-area input:focus {
                outline: none;
                border-color: #e94560;
            }
            #input-area button {
                padding: 12px 24px;
                background: #e94560;
                color: white;
                border: none;
                border-radius: 8px;
                cursor: pointer;
                font-weight: bold;
            }
            #input-area button:hover { background: #d63850; }
            #input-area button:disabled { background: #666; cursor: not-allowed; }
        </style>
    </head>
    <body>
        <header>
            <h1>🤖 SAISA</h1>
            <span class="badge">llama3.2</span>
        </header>
        <div id="chat">
            <div class="message bot">Salut! Je suis SAISA. Comment puis-je t'aider?</div>
        </div>
        <div id="input-area">
            <input type="text" id="user-input" placeholder="Tape ton message..." autofocus>
            <button id="send-btn">Envoyer</button>
        </div>
        <script>
            const chat = document.getElementById('chat');
            const input = document.getElementById('user-input');
            const btn = document.getElementById('send-btn');
            
            let history = [];
            
            function addMessage(text, isUser) {
                const div = document.createElement('div');
                div.className = 'message ' + (isUser ? 'user' : 'bot');
                div.textContent = text;
                chat.appendChild(div);
                chat.scrollTop = chat.scrollHeight;
            }
            
            async function send() {
                const text = input.value.trim();
                if (!text) return;
                
                addMessage(text, true);
                input.value = '';
                
                const typing = document.createElement('div');
                typing.className = 'message bot typing';
                typing.textContent = 'SAISA écrit...';
                chat.appendChild(typing);
                chat.scrollTop = chat.scrollHeight;
                
                btn.disabled = true;
                
                try {
                    const response = await fetch('/chat', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({message: text, history: history})
                    });
                    const data = await response.json();
                    typing.remove();
                    addMessage(data.response, false);
                    history.push([text, data.response]);
                } catch (e) {
                    typing.remove();
                    addMessage('Erreur: ' + e, false);
                }
                
                btn.disabled = false;
                input.focus();
            }
            
            btn.onclick = send;
            input.onkeypress = (e) => { if (e.key === 'Enter') send(); };
        </script>
    </body>
    </html>
    """
    
    @app.route('/')
    def index():
        return render_template_string(HTML_TEMPLATE)
    
    @app.route('/chat', methods=['POST'])
    def chat_route():
        data = request.json
        response = chat(data.get('message', ''), data.get('history'))
        return jsonify({'response': response})
    
    def run():
        print("="*50)
        print("  🌐 SAISA Web Interface")
        print(" :Ouvre: http://localhost:7860")
        print("="*50)
        app.run(host='0.0.0.0', port=7860, debug=False)

if __name__ == "__main__":
    if HAS_FLASK:
        run()
    else:
        print("Installer Flask: pip install flask")