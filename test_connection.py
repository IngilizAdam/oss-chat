#!/usr/bin/env python3
"""
OSS Chat Connection Test

Quick script to test connection to Ollama server from Isaac Sim environment.
"""

import json
import urllib.request
import urllib.error


def test_ollama_connection(host="http://192.168.1.11:11500"):
    """Test connection to Ollama server"""
    print(f"🔍 Testing connection to: {host}")
    
    try:
        # Test basic connectivity
        req = urllib.request.Request(f"{host}/api/tags")
        req.add_header('User-Agent', 'OSS-Chat-Test/1.0')
        req.add_header('Accept', 'application/json')
        
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                print("✅ Connection successful!")
                
                # Parse and display models
                data = json.loads(response.read().decode())
                models = data.get("models", [])
                
                if models:
                    print(f"📦 Found {len(models)} models:")
                    for model in models:
                        name = model.get("name", "Unknown")
                        size = model.get("size", 0)
                        size_gb = size / (1024**3) if size else 0
                        print(f"   - {name} ({size_gb:.1f}GB)")
                else:
                    print("⚠️ No models found. Pull some models first:")
                    print("   ollama pull llama3.2")
                    print("   ollama pull mistral")
                
                return True
                
            else:
                print(f"❌ HTTP Error: {response.status}")
                return False
                
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP Error: {e.code} - {e.reason}")
        return False
        
    except urllib.error.URLError as e:
        print(f"❌ Connection Error: {str(e)}")
        print("\n🔧 Troubleshooting tips:")
        print("1. Check if Ollama is running on the target server")
        print("2. Verify the server allows external connections:")
        print("   export OLLAMA_HOST=0.0.0.0:11434")
        print("3. Check firewall settings on the server")
        print("4. Verify the IP address is correct")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False


def test_chat_functionality(host="http://192.168.1.11:11500", model="llama3.2"):
    """Test actual chat functionality"""
    print(f"\n🧪 Testing chat with model: {model}")
    
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": "Say 'Connection test successful!' if you receive this."}
        ],
        "stream": False
    }
    
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            f"{host}/api/chat",
            data=data,
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'OSS-Chat-Test/1.0'
            }
        )
        
        with urllib.request.urlopen(req, timeout=60) as response:
            if response.status == 200:
                result = json.loads(response.read().decode())
                reply = result.get('message', {}).get('content', 'No response')
                print(f"✅ Chat test successful!")
                print(f"📝 Model response: {reply[:100]}...")
                return True
            else:
                print(f"❌ Chat failed: HTTP {response.status}")
                return False
                
    except Exception as e:
        print(f"❌ Chat test failed: {str(e)}")
        return False


def main():
    print("🚀 OSS Chat Connection Test")
    print("=" * 50)
    
    # You can modify this host to match your setup
    OLLAMA_HOST = "http://192.168.1.11:11500"
    
    # Test connection
    if test_ollama_connection(OLLAMA_HOST):
        # If connection works, test chat
        test_chat_functionality(OLLAMA_HOST)
    
    print("\n" + "=" * 50)
    print("Test complete. If connection failed, check CONFIGURATION.md for setup tips.")


if __name__ == "__main__":
    main()
