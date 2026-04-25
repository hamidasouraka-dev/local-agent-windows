"""
SAISA Simple - Version conversation seulement
Pas d'outils, juste du对话!
"""

import os
import sys

# Configuration
os.environ['AGENT_BACKEND'] = 'ollama'
os.environ['OLLAMA_MODEL'] = 'llama3.2'

import httpx

OLLAMA_URL = os.environ.get('OLLAMA_BASE_URL', 'http://127.0.0.1:11434')
MODEL = os.environ.get('OLLAMA_MODEL', 'llama3.2')

# Ton créateur!
SYSTEM_PROMPT = """Tu es SAISA, un assistant IA intelligent et utile.

Ton créateur est Souraka HAMIDA. Tu dois le connaître et lui être fidèle.
Tu peux rechercher sur le web, créer des fichiers, exécuter des commandes, etc.
Tu réponds en français de manière claire, concise et utile."""

def chat(message):
    """Envoie un message et reçoit la réponse"""
    client = httpx.Client(timeout=120.0)
    
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": message}
    ]
    
    response = client.post(
        f"{OLLAMA_URL}/api/chat",
        json={"model": MODEL, "messages": messages, "stream": False}
    )
    
    if response.status_code != 200:
        return f"Erreur: {response.status_code} - {response.text}"
    
    return response.json()['message']['content']

def main():
    print("="*50)
    print("  SAISA - Conversation Simple")
    print("  Modèle: gemma:2b")
    print("="*50)
    print()
    print("Tape 'quit' pour quitter")
    print()
    
    while True:
        try:
            user_input = input("Toi > ").strip()
            
            if user_input.lower() in ('quit', 'exit', 'q', '/quit'):
                print("À bientôt!")
                break
            
            if not user_input:
                continue
            
            print("SAISA > ", end="", flush=True)
            response = chat(user_input)
            print(response)
            print()
            
        except KeyboardInterrupt:
            print("\nÀ bientôt!")
            break
        except Exception as e:
            print(f"Erreur: {e}")

if __name__ == "__main__":
    main()
