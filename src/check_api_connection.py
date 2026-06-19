import sys
import requests

if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"

def main():
    print("Testing connection to LM Studio...")
    try:
        # Check active models
        models_resp = requests.get("http://localhost:1234/v1/models", timeout=5)
        if models_resp.status_code == 200:
            print("Connected successfully! Loaded models:")
            print(models_resp.json())
        else:
            print(f"Server returned status {models_resp.status_code}")
    except Exception as e:
        print(f"Could not retrieve loaded models: {e}")

    # Send a simple greeting text message
    payload = {
        "model": "local-model",
        "messages": [
            {
                "role": "user",
                "content": "Hello! Please reply with exactly: 'Model is active and ready!'"
            }
        ],
        "temperature": 0.1,
        "max_tokens": 50
    }
    
    headers = {"Content-Type": "application/json"}
    
    print("\nSending test prompt to model...")
    try:
        response = requests.post(LM_STUDIO_URL, headers=headers, json=payload, timeout=60)
        if response.status_code == 200:
            answer = response.json()['choices'][0]['message']['content'].strip()
            print("\nResponse from local model:")
            print(f"'{answer}'")
        else:
            print(f"Error (Status {response.status_code}): {response.text}")
    except Exception as e:
        print(f"Error communicating with local server: {e}")

if __name__ == "__main__":
    main()
