# SPDX-FileCopyrightText: Copyright (c) 2022-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import asyncio
import json
import threading
from typing import Callable, Dict, List, Optional

try:
    import carb
except ImportError:
    # Fallback logging for development
    class MockCarb:
        def log_error(self, msg):
            print(f"ERROR: {msg}")
        def log_info(self, msg):
            print(f"INFO: {msg}")
    carb = MockCarb()

from .global_variables import SYSTEM_PROMPT


class ChatMessage:
    def __init__(self, role: str, content: str, timestamp: Optional[str] = None):
        self.role = role  # "user" or "assistant"
        self.content = content
        self.timestamp = timestamp or self._get_current_time()
    
    def _get_current_time(self):
        import datetime
        return datetime.datetime.now().strftime("%H:%M:%S")
    
    def to_dict(self):
        return {
            "role": self.role,
            "content": self.content
        }


class OllamaChatService:
    def __init__(self, host: str = "http://localhost:11434"):
        self.host = host.rstrip("/")
        self.current_model = None
        self.conversation_history: List[ChatMessage] = []
        self._is_generating = False
        self._initialize_with_system_prompt()
        
    def _initialize_with_system_prompt(self):
        """Initialize conversation with system prompt"""
        if SYSTEM_PROMPT.strip():
            self.conversation_history = [ChatMessage("system", SYSTEM_PROMPT)]
        else:
            self.conversation_history = []
        
    def set_model(self, model_name: str):
        """Set the current model to use for chat"""
        self.current_model = model_name
        
    def clear_conversation(self):
        """Clear the conversation history but keep system prompt"""
        self._initialize_with_system_prompt()
        
    def add_message(self, role: str, content: str) -> ChatMessage:
        """Add a message to the conversation history"""
        message = ChatMessage(role, content)
        self.conversation_history.append(message)
        return message
        
    async def get_available_models(self) -> List[str]:
        """Get list of available models from Ollama"""
        try:
            # Try using urllib for HTTP requests (built-in Python library)
            import urllib.request
            import urllib.error
            
            carb.log_info(f"Fetching models from: {self.host}/api/tags")
            
            try:
                # Create request with timeout and proper headers
                req = urllib.request.Request(f"{self.host}/api/tags")
                req.add_header('User-Agent', 'OSS-Chat-Extension/1.0')
                req.add_header('Accept', 'application/json')
                
                with urllib.request.urlopen(req, timeout=15) as response:
                    if response.status == 200:
                        data = json.loads(response.read().decode())
                        models = [model["name"] for model in data.get("models", [])]
                        carb.log_info(f"Found {len(models)} models: {models}")
                        return models
                    else:
                        carb.log_error(f"Failed to get models: HTTP {response.status}")
                        return ["llama3.2", "llama2", "mistral"]  # Default fallback models
                        
            except urllib.error.HTTPError as e:
                carb.log_error(f"HTTP Error getting models: {e.code} - {e.reason}")
                return ["llama3.2", "llama2", "mistral"]  # Default fallback models
            except urllib.error.URLError as e:
                carb.log_error(f"URL Error getting models: {str(e)}")
                return ["llama3.2", "llama2", "mistral"]  # Default fallback models
            except json.JSONDecodeError as e:
                carb.log_error(f"JSON decode error: {str(e)}")
                return ["llama3.2", "llama2", "mistral"]  # Default fallback models
                
        except Exception as e:
            carb.log_error(f"Error getting models: {str(e)}")
            return ["llama3.2", "llama2", "mistral"]  # Default fallback models
    
    def send_message_sync(self, message: str, callback: Callable[[str, bool], None]):
        """Send a message synchronously in a separate thread, streaming response."""
        def _send_message():
            try:
                import http.client
                from urllib.parse import urlparse
                
                if not self.current_model:
                    callback("Error: No model selected", True)
                    return
                
                # Add user message to history
                self.add_message("user", message)
                
                # Prepare the request
                url = f"{self.host}/api/chat"
                payload = {
                    "model": self.current_model,
                    "messages": [msg.to_dict() for msg in self.conversation_history],
                    "stream": True  # Enable streaming
                }
                self._is_generating = True
                response_content = ""
                try:
                    carb.log_info(f"Streaming message to: {url}")
                    parsed = urlparse(url)
                    conn_cls = http.client.HTTPSConnection if parsed.scheme == "https" else http.client.HTTPConnection
                    conn = conn_cls(parsed.hostname, parsed.port or (443 if parsed.scheme == "https" else 80), timeout=120)
                    headers = {
                        "Content-Type": "application/json",
                        "User-Agent": "OSS-Chat-Extension/1.0",
                        "Accept": "application/json"
                    }
                    conn.request("POST", parsed.path, body=json.dumps(payload), headers=headers)
                    resp = conn.getresponse()
                    if resp.status != 200:
                        callback(f"Error: Server returned status {resp.status}", True)
                        return
                    # Read the response as a stream
                    for line in resp:
                        if not line:
                            continue
                        try:
                            json_response = json.loads(line.decode('utf-8'))
                        except Exception:
                            continue
                        if 'message' in json_response:
                            content = json_response['message'].get('content', '')
                            if content:
                                response_content += content
                                callback(response_content, False)  # Partial response
                        if json_response.get('done', False):
                            break
                    # Add assistant response to history
                    if response_content:
                        self.add_message("assistant", response_content)
                        callback(response_content, True)  # Final response
                    else:
                        callback("Error: Empty response from model", True)
                except Exception as e:
                    error_msg = f"Streaming error: {str(e)}"
                    carb.log_error(error_msg)
                    callback(error_msg, True)
                finally:
                    self._is_generating = False
            except Exception as e:
                error_msg = f"Unexpected error: {str(e)}"
                carb.log_error(error_msg)
                callback(error_msg, True)
        # Run in separate thread to avoid blocking UI
        thread = threading.Thread(target=_send_message)
        thread.daemon = True
        thread.start()
    
    def is_generating(self) -> bool:
        """Check if currently generating a response"""
        return self._is_generating
    
    def stop_generation(self):
        """Stop the current generation (basic implementation)"""
        self._is_generating = False
        
    async def test_connection(self) -> bool:
        """Test connection to Ollama server"""
        try:
            import urllib.request
            import urllib.error
            
            carb.log_info(f"Testing connection to: {self.host}/api/tags")
            
            try:
                # Create request with timeout
                req = urllib.request.Request(f"{self.host}/api/tags")
                req.add_header('User-Agent', 'OSS-Chat-Extension/1.0')
                
                with urllib.request.urlopen(req, timeout=10) as response:
                    if response.status == 200:
                        carb.log_info("Connection test successful")
                        return True
                    else:
                        carb.log_error(f"Connection test failed with status: {response.status}")
                        return False
                        
            except urllib.error.HTTPError as e:
                carb.log_error(f"HTTP Error during connection test: {e.code} - {e.reason}")
                return False
            except urllib.error.URLError as e:
                carb.log_error(f"URL Error during connection test: {str(e)}")
                return False
            except Exception as e:
                carb.log_error(f"Unexpected error during connection test: {str(e)}")
                return False
                
        except Exception as e:
            carb.log_error(f"Connection test failed: {str(e)}")
            return False
