#!/usr/bin/env python3
"""
OSS Chat Setup Helper

This script helps users set up Ollama and verify the installation works
with the OSS Chat extension.
"""

import json
import subprocess
import sys
import urllib.request
import urllib.error


def check_ollama_installation():
    """Check if Ollama is installed"""
    try:
        result = subprocess.run(["ollama", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Ollama is installed: {result.stdout.strip()}")
            return True
        else:
            print("❌ Ollama is not installed or not in PATH")
            return False
    except FileNotFoundError:
        print("❌ Ollama is not installed or not in PATH")
        return False


def check_ollama_service():
    """Check if Ollama service is running"""
    try:
        with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=5) as response:
            if response.status == 200:
                print("✅ Ollama service is running")
                return True
            else:
                print(f"❌ Ollama service returned status: {response.status}")
                return False
    except urllib.error.URLError:
        print("❌ Ollama service is not running")
        return False
    except Exception as e:
        print(f"❌ Error checking Ollama service: {e}")
        return False


def get_installed_models():
    """Get list of installed models"""
    try:
        with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=10) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                models = [model["name"] for model in data.get("models", [])]
                if models:
                    print("✅ Installed models:")
                    for model in models:
                        print(f"   - {model}")
                    return models
                else:
                    print("❌ No models installed")
                    return []
            else:
                print(f"❌ Failed to get models: {response.status}")
                return []
    except Exception as e:
        print(f"❌ Error getting models: {e}")
        return []


def install_recommended_models():
    """Install recommended models"""
    recommended = ["llama3.2", "mistral"]
    
    print("\n📥 Installing recommended models...")
    print("This may take a while depending on your internet connection.")
    
    for model in recommended:
        print(f"\nInstalling {model}...")
        try:
            result = subprocess.run(["ollama", "pull", model], check=True)
            print(f"✅ Successfully installed {model}")
        except subprocess.CalledProcessError:
            print(f"❌ Failed to install {model}")
        except KeyboardInterrupt:
            print("\n⏹️ Installation interrupted by user")
            break


def test_chat():
    """Test chat functionality"""
    print("\n🧪 Testing chat functionality...")
    
    test_message = {
        "model": "llama3.2",
        "messages": [{"role": "user", "content": "Hello! Say 'OSS Chat setup test successful' if you can see this."}],
        "stream": False
    }
    
    try:
        data = json.dumps(test_message).encode('utf-8')
        req = urllib.request.Request(
            "http://localhost:11434/api/chat",
            data=data,
            headers={'Content-Type': 'application/json'}
        )
        
        with urllib.request.urlopen(req, timeout=30) as response:
            if response.status == 200:
                result = json.loads(response.read().decode())
                reply = result.get('message', {}).get('content', '')
                print(f"✅ Chat test successful!")
                print(f"   Model response: {reply[:100]}...")
                return True
            else:
                print(f"❌ Chat test failed: {response.status}")
                return False
                
    except Exception as e:
        print(f"❌ Chat test failed: {e}")
        return False


def main():
    print("🚀 OSS Chat Setup Helper")
    print("=" * 50)
    
    # Check installation
    ollama_installed = check_ollama_installation()
    if not ollama_installed:
        print("\n📋 To install Ollama:")
        print("   Visit: https://ollama.ai/")
        print("   Follow the installation instructions for your OS")
        return False
    
    # Check service
    service_running = check_ollama_service()
    if not service_running:
        print("\n📋 To start Ollama service:")
        print("   Run: ollama serve")
        print("   Or check if it's running as a system service")
        return False
    
    # Check models
    models = get_installed_models()
    if not models:
        print("\n❓ Would you like to install recommended models? (y/n): ", end="")
        if input().lower().startswith('y'):
            install_recommended_models()
            models = get_installed_models()
    
    # Test chat if models are available
    if models:
        if "llama3.2" in models:
            test_chat()
        else:
            print(f"\n💡 You can test chat with any installed model")
    
    print("\n🎉 Setup complete!")
    print("You can now use the OSS Chat extension in Isaac Sim.")
    print("\n📖 For more information, see the README.md file.")
    
    return True


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Setup interrupted by user")
        sys.exit(1)
