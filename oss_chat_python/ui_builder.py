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
from typing import List

import omni.ui as ui
from isaacsim.gui.components.element_wrappers import (
    Button,
    CollapsableFrame,
    DropDown,
    StringField,
    TextBlock,
)
from isaacsim.gui.components.ui_utils import get_style

from .chat_service import OllamaChatService
from .global_variables import DEFAULT_OLLAMA_HOST, DEFAULT_MODEL


class UIBuilder:
    def __init__(self):
        # Frames are sub-windows that can contain multiple UI elements
        self.frames = []
        
        # UI elements created using a UIElementWrapper from isaacsim.gui.components.element_wrappers
        self.wrapped_ui_elements = []
        
        # Chat service
        self.chat_service = OllamaChatService(DEFAULT_OLLAMA_HOST)
        self.chat_service.set_model(DEFAULT_MODEL)
        
        # Chat UI elements
        self.chat_history_field = None
        self.message_input_field = None
        self.model_dropdown = None
        self.send_button = None
        self.clear_button = None
        self.ollama_host_field = None
        self.connection_status_field = None
        
        # Chat state
        self.is_waiting_for_response = False

    ###################################################################################
    #           The Functions Below Are Called Automatically By extension.py
    ###################################################################################

    def on_menu_callback(self):
        """Callback for when the UI is opened from the toolbar.
        This is called directly after build_ui().
        """
        # Test connection when UI is opened
        asyncio.ensure_future(self._test_connection())
        asyncio.ensure_future(self._load_models())

    def on_timeline_event(self, event):
        """Callback for Timeline events (Play, Pause, Stop)

        Args:
            event (omni.timeline.TimelineEventType): Event Type
        """
        pass

    def on_physics_step(self, step):
        """Callback for Physics Step.
        Physics steps only occur when the timeline is playing

        Args:
            step (float): Size of physics step
        """
        pass

    def on_stage_event(self, event):
        """Callback for Stage Events

        Args:
            event (omni.usd.StageEventType): Event Type
        """
        pass

    def cleanup(self):
        """
        Called when the stage is closed or the extension is hot reloaded.
        Perform any necessary cleanup such as removing active callback functions
        """
        for ui_elem in self.wrapped_ui_elements:
            ui_elem.cleanup()

    def build_ui(self):
        """
        Build a chat UI to interact with LLM models through Ollama.
        """
        self._create_connection_frame()
        self._create_model_selection_frame()
        self._create_chat_frame()
        self._create_controls_frame()

    def _create_connection_frame(self):
        """Create the connection configuration frame"""
        connection_frame = CollapsableFrame("Connection Settings", collapsed=True)
        self.frames.append(connection_frame)
        
        with connection_frame:
            with ui.VStack(style=get_style(), spacing=5, height=0):
                self.ollama_host_field = StringField(
                    "Ollama Host",
                    default_value=DEFAULT_OLLAMA_HOST,
                    tooltip="URL of the Ollama server (e.g., http://localhost:11434)",
                    read_only=False,
                    multiline_okay=False,
                    on_value_changed_fn=self._on_host_changed,
                )
                self.wrapped_ui_elements.append(self.ollama_host_field)
                
                self.connection_status_field = TextBlock(
                    "Connection Status",
                    text="Not connected",
                    num_lines=1,
                    tooltip="Shows the current connection status to Ollama",
                )
                
                test_connection_button = Button(
                    "Test Connection",
                    "Test Connection",
                    tooltip="Test connection to the Ollama server",
                    on_click_fn=self._on_test_connection,
                )
                self.wrapped_ui_elements.append(test_connection_button)

    def _create_model_selection_frame(self):
        """Create the model selection frame"""
        model_frame = CollapsableFrame("Model Selection", collapsed=False)
        self.frames.append(model_frame)
        
        with model_frame:
            with ui.VStack(style=get_style(), spacing=5, height=0):
                def model_populate_fn():
                    return ["llama3.2", "llama2", "mistral"]  # Default models
                
                self.model_dropdown = DropDown(
                    "Model",
                    tooltip="Select a model to chat with",
                    populate_fn=model_populate_fn,
                    on_selection_fn=self._on_model_selection,
                )
                self.wrapped_ui_elements.append(self.model_dropdown)

    def _create_chat_frame(self):
        """Create the main chat interface frame"""
        chat_frame = CollapsableFrame("Chat", collapsed=False)
        self.frames.append(chat_frame)
        
        with chat_frame:
            with ui.VStack(style=get_style(), spacing=5, height=0):
                # Chat history display
                self.chat_history_field = TextBlock(
                    "Chat History",
                    text="Welcome to OSS Chat! 🤖\n\nI'm your AI assistant integrated with Isaac Sim, ready to help with robotics simulation, programming, and technical questions.\n\nSelect a model and start chatting!\n\nMake sure Ollama is running and accessible.",
                    num_lines=15,
                    tooltip="Chat conversation history",
                    include_copy_button=True,
                )
                
                # Message input
                self.message_input_field = StringField(
                    "Message",
                    default_value="",
                    tooltip="Type your message here and press Enter or click Send",
                    read_only=False,
                    multiline_okay=True,
                    on_value_changed_fn=self._on_message_input,
                )
                self.wrapped_ui_elements.append(self.message_input_field)

    def _create_controls_frame(self):
        """Create the control buttons frame"""
        controls_frame = CollapsableFrame("Controls", collapsed=False)
        self.frames.append(controls_frame)
        
        with controls_frame:
            with ui.VStack(style=get_style(), spacing=5, height=0):
                with ui.HStack():
                    self.send_button = Button(
                        "Send",
                        "Send Message",
                        tooltip="Send the message to the selected model",
                        on_click_fn=self._on_send_message,
                    )
                    self.wrapped_ui_elements.append(self.send_button)
                    
                    self.clear_button = Button(
                        "Clear",
                        "Clear Chat",
                        tooltip="Clear the chat history",
                        on_click_fn=self._on_clear_chat,
                    )
                    self.wrapped_ui_elements.append(self.clear_button)

    ###################################################################################
    #           Chat-specific callback functions
    ###################################################################################

    def _on_host_changed(self, new_host: str):
        """Callback when Ollama host is changed"""
        self.chat_service.host = new_host.rstrip("/")
        # Only update host, do not test connection or load models automatically

    def _on_test_connection(self):
        """Callback for test connection button"""
        asyncio.ensure_future(self._test_connection())
        asyncio.ensure_future(self._load_models())

    def _on_model_selection(self, model_name: str):
        """Callback when a model is selected"""
        self.chat_service.set_model(model_name)
        self._update_chat_display()
        self._append_to_chat(f"\n--- 🔄 Switched to model: {model_name} ---")
        self._append_to_chat(f"\n💡 I'm specialized for Isaac Sim and robotics questions!\n")

    def _on_message_input(self, message: str):
        """Callback when message input changes"""
        # Handle Enter key press (basic implementation)
        pass

    def _on_send_message(self):
        """Callback for send message button"""
        try:
            if self.is_waiting_for_response:
                self._append_to_chat("⏳ Please wait for the current response to complete.\n")
                return
                
            if not self.message_input_field:
                self._append_to_chat("❌ Error: Message input field not available.\n")
                return
                
            message = self.message_input_field.get_value().strip()
            if not message:
                self._append_to_chat("⚠️ Please enter a message.\n")
                return
                
            if not self.chat_service.current_model:
                self._append_to_chat("❌ Error: Please select a model first.\n")
                return
            
            # Clear input field
            self.message_input_field.set_value("")
            
            # Add user message to chat display
            self._append_to_chat(f"\n🧑 You: {message}\n")
            self._append_to_chat("🤖 Assistant: ")
            
            # Disable send button while waiting (by setting flag)
            self.is_waiting_for_response = True
            
            # Send message to chat service
            self.chat_service.send_message_sync(message, self._on_message_response)
            
        except Exception as e:
            error_msg = f"❌ Error sending message: {str(e)}"
            self._append_to_chat(f"\n{error_msg}\n")
            self.is_waiting_for_response = False

    def _on_clear_chat(self):
        """Callback for clear chat button"""
        self.chat_service.clear_conversation()
        if self.chat_history_field:
            self.chat_history_field.set_text("Chat cleared! 🧹\n\nI'm ready to help with Isaac Sim, robotics, and simulation questions.\nStart a new conversation!")
        self._update_status("Chat history cleared")

    def _on_message_response(self, response: str, is_final: bool):
        """Callback for when a response is received from the chat service"""
        if is_final:
            # Final response - enable send button and update full response
            self.is_waiting_for_response = False
            # Note: Button enabled state will be checked in _on_send_message
            
            # Update the last assistant message in the chat display
            if self.chat_history_field:
                current_text = self.chat_history_field.get_text()
                lines = current_text.split('\n')
                
                # Find the last "Assistant:" line and replace everything after it
                for i in range(len(lines) - 1, -1, -1):
                    if "🤖 Assistant:" in lines[i]:
                        lines[i] = f"🤖 Assistant: {response}"
                        # Remove any lines after this assistant response
                        lines = lines[:i+1]
                        break
                
                updated_text = '\n'.join(lines) + '\n'
                self.chat_history_field.set_text(updated_text)
        else:
            # Partial response - update the display incrementally
            self._update_assistant_response(response)

    def _append_to_chat(self, text: str):
        """Append text to the chat history display"""
        if self.chat_history_field:
            current_text = self.chat_history_field.get_text()
            self.chat_history_field.set_text(current_text + text)

    def _update_assistant_response(self, response: str):
        """Update the current assistant response in the chat display"""
        if self.chat_history_field:
            current_text = self.chat_history_field.get_text()
            lines = current_text.split('\n')
            
            # Find the last "Assistant:" line and update it
            for i in range(len(lines) - 1, -1, -1):
                if "🤖 Assistant:" in lines[i]:
                    lines[i] = f"🤖 Assistant: {response}"
                    break
            
            updated_text = '\n'.join(lines)
            self.chat_history_field.set_text(updated_text)

    def _update_chat_display(self):
        """Update the chat display with current conversation history"""
        if not self.chat_service.conversation_history or not self.chat_history_field:
            return
            
        chat_text = ""
        for message in self.chat_service.conversation_history:
            # Skip system messages in the display (they're used internally)
            if message.role == "system":
                continue
            elif message.role == "user":
                chat_text += f"\n🧑 You: {message.content}\n"
            elif message.role == "assistant":
                chat_text += f"🤖 Assistant: {message.content}\n"
        
        self.chat_history_field.set_text(chat_text)

    def _update_status(self, message: str):
        """Update the connection status"""
        if self.connection_status_field:
            self.connection_status_field.set_text(message)

    async def _test_connection(self):
        """Test connection to Ollama server"""
        self._update_status("Testing connection...")
        try:
            is_connected = await self.chat_service.test_connection()
            if is_connected:
                self._update_status("✅ Connected to Ollama")
            else:
                self._update_status(f"❌ Connection failed to {self.chat_service.host}")
                # Also show in chat
                self._append_to_chat(f"\n⚠️ Connection failed to {self.chat_service.host}\n")
                self._append_to_chat("Please check:\n")
                self._append_to_chat("1. Ollama is running on the target server\n")
                self._append_to_chat("2. The server allows connections from your IP\n")
                self._append_to_chat("3. No firewall is blocking port 11434\n\n")
        except Exception as e:
            error_msg = f"❌ Connection error: {str(e)}"
            self._update_status(error_msg)
            self._append_to_chat(f"\n⚠️ Connection error: {str(e)}\n\n")

    async def _load_models(self):
        """Load available models from Ollama"""
        try:
            models = await self.chat_service.get_available_models()
            if models and self.model_dropdown:
                # Update dropdown with available models
                def model_populate_fn():
                    return models
                
                self.model_dropdown._populate_fn = model_populate_fn
                self.model_dropdown.repopulate()
                
                # Set first model as default if none selected
                if not self.chat_service.current_model and models:
                    self.chat_service.set_model(models[0])
                    
                # Show success in chat
                if len(models) > 3:  # More than just fallback models
                    self._append_to_chat(f"📦 Loaded {len(models)} models from Ollama server\n\n")
                else:
                    self._append_to_chat(f"⚠️ Using fallback models. Check connection to load actual models.\n\n")
        except Exception as e:
            error_msg = f"Error loading models: {str(e)}"
            self._append_to_chat(f"\n⚠️ {error_msg}\n\n")
