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
        
        # New message-based chat system
        self.chat_messages = []
        self.chat_container = None

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
                
                self.connection_status_field = ui.Label(
                    "Not connected",
                    height=20,
                    tooltip="Shows the current connection status to Ollama",
                    style={
                        "color": 0xFFCCCCCC,
                        "font_size": 12,
                    }
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
                # Chat history header with copy button
                with ui.HStack(height=25):
                    ui.Label("Chat History", height=20)
                    ui.Spacer()
                    self._copy_button = ui.Button("Copy All", width=80, height=20)
                    self._copy_button.set_clicked_fn(self._copy_chat_to_clipboard)
                
                # Create a scrollable chat area with multiple UI elements approach
                with ui.ScrollingFrame(
                    height=400,  # Increased height for better visibility
                    horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_AS_NEEDED,
                    vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_ON,
                    style={
                        "ScrollingFrame": {
                            "background_color": 0x23212121,
                            "border_color": 0x33444444,
                            "border_width": 1,
                            "border_radius": 4,
                        }
                    }
                ):
                    # Create a VStack to hold individual message elements with more spacing
                    self.chat_container = ui.VStack(spacing=8)  # Increased spacing between messages
                    with self.chat_container:
                        # Add welcome message as a label
                        welcome_text = (
                            "=== Welcome to OSS Chat! ===\n"
                            "=" * 50 + "\n\n"
                            "I'm your AI assistant integrated with Isaac Sim, ready to help with:\n"
                            "* Robotics simulation\n"
                            "* Programming & scripting\n"
                            "* Technical questions\n" 
                            "* Isaac Sim documentation\n\n"
                            "NEW FEATURES:\n"
                            "* Full text selection & copying\n" 
                            "* Scrollable chat history\n"
                            "* Enhanced formatting\n\n"
                            "TIP: Use the 'Copy All' button to copy the entire chat!\n\n"
                            "Setup: Select a model and start chatting!\n"
                            "Make sure Ollama is running and accessible."
                        )
                        
                        # Store messages as a list for better management
                        self.chat_messages = []
                        self._add_welcome_message(welcome_text)
                
                # Message input with enhanced styling
                self.message_input_field = StringField(
                    "Message",
                    default_value="",
                    tooltip="Type your message here. Press Ctrl+Enter for new line, Enter to send (when implemented)",
                    read_only=False,
                    multiline_okay=True,
                    on_value_changed_fn=self._on_message_input,
                )
                self.wrapped_ui_elements.append(self.message_input_field)

    def _add_welcome_message(self, text):
        """Add the welcome message to chat"""
        if hasattr(self, 'chat_container') and self.chat_container:
            with self.chat_container:
                ui.Label(
                    text, 
                    word_wrap=True,
                    style={
                        "color": 0xFFCCCCCC,
                        "font_size": 12,
                        "margin": 5,
                        "padding": 5
                    }
                )

    def _add_message_to_chat(self, sender, message, message_type="normal"):
        """Add a message to the chat display as a separate UI element"""
        if not hasattr(self, 'chat_container') or not self.chat_container:
            return
            
        # Choose styling based on message type
        if message_type == "user":
            color = 0xFF88AAFF  # Light blue for user
            prefix = "You: "
        elif message_type == "assistant":
            color = 0xFF88FF88  # Light green for assistant  
            prefix = "Assistant: "
        elif message_type == "system":
            color = 0xFFFFAA88  # Light orange for system
            prefix = "System: "
        else:
            color = 0xFFCCCCCC  # Default white
            prefix = f"{sender}: " if sender else ""
        
        display_text = prefix + message
        
        try:
            with self.chat_container:
                # Add a subtle separator for better visual separation (except for first message)
                if hasattr(self, 'chat_messages') and self.chat_messages:
                    ui.Spacer(height=3)
                    ui.Rectangle(height=1, style={"background_color": 0x22444444})
                    ui.Spacer(height=3)
                
                # Create a selectable text field for each message
                # Calculate proper height based on content length
                lines = display_text.split('\n')
                estimated_lines = max(1, len(lines))
                
                # Add extra lines for text wrapping (approximate 80 chars per line)
                for line in lines:
                    if len(line) > 80:
                        estimated_lines += (len(line) // 80)
                
                # Set minimum height and scale with content
                min_height = 30  # Increased minimum height
                line_height = 20  # Slightly increased line height for better readability
                calculated_height = max(min_height, estimated_lines * line_height)
                
                # Cap maximum height to prevent extremely tall boxes
                max_height = 400 if message_type == "assistant" else 200  # Increased max heights
                final_height = min(calculated_height, max_height)
                
                message_field = ui.StringField(
                    multiline=True,
                    read_only=True,
                    height=ui.Pixel(final_height),
                    style={
                        "StringField": {
                            "background_color": 0x15000000,  # Slightly more visible background
                            "border_width": 1,
                            "border_color": 0x22444444,  # Subtle border
                            "border_radius": 3,
                            "color": color,
                            "font_size": 12,
                            "margin": 3,
                            "padding": 8  # Increased padding for better readability
                        }
                    }
                )
                
                # Set the message text with safe encoding
                try:
                    # Convert any problematic characters to safe alternatives
                    safe_text = display_text.encode('ascii', errors='replace').decode('ascii')
                    message_field.model.set_value(safe_text)
                except Exception:
                    message_field.model.set_value(str(display_text))
                
                # Store reference for copying functionality
                if not hasattr(self, 'chat_messages'):
                    self.chat_messages = []
                
                self.chat_messages.append({
                    'field': message_field,
                    'text': display_text,
                    'type': message_type
                })
        except Exception as e:
            # Fallback if container is not available
            print(f"Could not add message to chat: {e}")

    def _update_message_field_height(self, field, text):
        """Update the height of a message field based on content"""
        try:
            lines = text.split('\n')
            estimated_lines = max(1, len(lines))
            
            # Add extra lines for text wrapping (approximate 80 chars per line)
            for line in lines:
                if len(line) > 80:
                    estimated_lines += (len(line) // 80)
            
            # Set minimum height and scale with content (matching _add_message_to_chat)
            min_height = 30
            line_height = 20
            calculated_height = max(min_height, estimated_lines * line_height)
            
            # Cap maximum height for assistant responses
            max_height = 400
            final_height = min(calculated_height, max_height)
            
            # Update the field height
            field.height = ui.Pixel(final_height)
            
        except Exception as e:
            # Fallback to a reasonable default height
            field.height = ui.Pixel(100)

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

    def _copy_chat_to_clipboard(self):
        """Copy the entire chat history to clipboard"""
        chat_text = self._get_all_chat_text()
        try:
            # Try to use system clipboard if available
            try:
                import tkinter as tk
                root = tk.Tk()
                root.withdraw()  # Hide the window
                root.clipboard_clear()
                root.clipboard_append(chat_text)
                root.update()
                root.destroy()
                self._add_message_to_chat("System", "Chat copied to clipboard!", "system")
            except ImportError:
                # Show a selectable text dialog as fallback
                self._show_copyable_text_dialog(chat_text)
        except Exception as e:
            # Fallback: Show the text in a new selectable dialog
            self._show_copyable_text_dialog(chat_text)

    def _show_copyable_text_dialog(self, text):
        """Show a dialog with selectable text for manual copying"""
        # Create a simple window with selectable text
        copy_window = ui.Window("Copy Chat History", width=500, height=400)
        with copy_window.frame:
            with ui.VStack(spacing=10):
                ui.Label("Select and copy the text below (Ctrl+A to select all):", height=20)
                text_field = ui.StringField(
                    multiline=True,
                    read_only=True,
                    height=ui.Percent(90),
                    style={
                        "StringField": {
                            "background_color": 0x23212121,
                            "border_color": 0x33444444, 
                            "border_width": 1,
                            "color": 0xFFCCCCCC,
                            "font_size": 12,
                            "padding": 8
                        }
                    }
                )
                text_field.model.set_value(text)
                
                def close_dialog():
                    copy_window.visible = False
                
                close_button = ui.Button("Close", height=30)
                close_button.set_clicked_fn(close_dialog)

    def _safe_set_text(self, text):
        """Safely set text with proper encoding handling"""
        if self.chat_history_field:
            try:
                # Ensure the text is properly encoded as UTF-8
                if isinstance(text, str):
                    # Replace problematic characters with ASCII alternatives
                    safe_text = text.encode('ascii', errors='replace').decode('ascii')
                    self.chat_history_field.model.set_value(safe_text)
                else:
                    self.chat_history_field.model.set_value(str(text))
            except Exception as e:
                # Fallback to simple string conversion
                self.chat_history_field.model.set_value(str(text))

    def _safe_get_text(self):
        """Safely get text with proper encoding handling"""
        if self.chat_history_field:
            try:
                return self.chat_history_field.model.get_value_as_string()
            except Exception:
                return ""
        return ""

    def _auto_scroll_to_bottom(self):
        """Auto-scroll the chat to the bottom"""
        # This is a placeholder for auto-scroll functionality
        # The ScrollingFrame should automatically scroll to bottom when content is added
        pass

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
        self._append_to_chat(f"\n--- Switched to model: {model_name} ---")
        self._append_to_chat(f"\nI'm specialized for Isaac Sim and robotics questions!\n")

    def _on_message_input(self, message: str):
        """Callback when message input changes"""
        # Handle Enter key press (basic implementation)
        pass

    def _on_send_message(self):
        """Callback for send message button"""
        try:
            if self.is_waiting_for_response:
                self._add_message_to_chat("System", "Please wait for the current response to complete.", "system")
                return
                
            if not self.message_input_field:
                self._add_message_to_chat("System", "ERROR: Message input field not available.", "system")
                return
                
            message = self.message_input_field.get_value().strip()
            if not message:
                self._add_message_to_chat("System", "WARNING: Please enter a message.", "system")
                return
                
            if not self.chat_service.current_model:
                self._add_message_to_chat("System", "ERROR: Please select a model first.", "system")
                return
            
            # Clear input field
            self.message_input_field.set_value("")
            
            # Add user message to chat display
            self._add_message_to_chat("You", message, "user")
            
            # Add placeholder for assistant response
            self._current_assistant_message_index = len(self.chat_messages)
            self._add_message_to_chat("Assistant", "...", "assistant")
            
            # Disable send button while waiting (by setting flag)
            self.is_waiting_for_response = True
            
            # Send message to chat service
            self.chat_service.send_message_sync(message, self._on_message_response)
            
        except Exception as e:
            error_msg = f"ERROR sending message: {str(e)}"
            self._add_message_to_chat("System", error_msg, "system")
            self.is_waiting_for_response = False

    def _on_clear_chat(self):
        """Callback for clear chat button"""
        self.chat_service.clear_conversation()
        self._clear_chat_messages()
        
        # Add welcome message back
        welcome_text = (
            "Chat cleared!\n\n"
            "I'm ready to help with Isaac Sim, robotics, and simulation questions.\n"
            "Start a new conversation!"
        )
        self._add_welcome_message(welcome_text)
        self._update_status("Chat history cleared")

    def _on_message_response(self, response: str, is_final: bool):
        """Callback for when a response is received from the chat service"""
        if is_final:
            # Final response - enable send button and update full response
            self.is_waiting_for_response = False
            # Update the last assistant message with the final response
            if hasattr(self, '_current_assistant_message_index') and hasattr(self, 'chat_messages'):
                if self._current_assistant_message_index < len(self.chat_messages):
                    msg = self.chat_messages[self._current_assistant_message_index]
                    if msg['field']:
                        try:
                            safe_response = response.encode('ascii', errors='replace').decode('ascii')
                            full_text = "Assistant: " + safe_response
                            msg['field'].model.set_value(full_text)
                            msg['text'] = "Assistant: " + response
                            # Update height based on content
                            self._update_message_field_height(msg['field'], full_text)
                        except Exception:
                            full_text = "Assistant: " + str(response)
                            msg['field'].model.set_value(full_text)
                            msg['text'] = "Assistant: " + str(response)
                            self._update_message_field_height(msg['field'], full_text)
        else:
            # Partial response - update the display incrementally
            self._update_assistant_response(response)

    def _append_to_chat(self, text: str):
        """Append text to the chat history display"""
        # For simple status messages, add as system messages
        self._add_message_to_chat("", text, "system")
        self._auto_scroll_to_bottom()

    def _clear_chat_messages(self):
        """Clear all chat messages"""
        if hasattr(self, 'chat_messages'):
            self.chat_messages.clear()
        # Clear the container
        if hasattr(self, 'chat_container') and self.chat_container:
            self.chat_container.clear()

    def _get_all_chat_text(self):
        """Get all chat text for copying"""
        if hasattr(self, 'chat_messages') and self.chat_messages:
            return '\n'.join([msg['text'] for msg in self.chat_messages])
        return "No chat history available."

    def _update_assistant_response(self, response: str):
        """Update the current assistant response in the chat display"""
        if hasattr(self, '_current_assistant_message_index') and hasattr(self, 'chat_messages'):
            if self._current_assistant_message_index < len(self.chat_messages):
                msg = self.chat_messages[self._current_assistant_message_index]
                if msg['field']:
                    try:
                        safe_response = response.encode('ascii', errors='replace').decode('ascii')
                        full_text = "Assistant: " + safe_response
                        msg['field'].model.set_value(full_text)
                        msg['text'] = "Assistant: " + response
                        # Update height based on content during streaming
                        self._update_message_field_height(msg['field'], full_text)
                    except Exception:
                        full_text = "Assistant: " + str(response)
                        msg['field'].model.set_value(full_text)
                        msg['text'] = "Assistant: " + str(response)
                        self._update_message_field_height(msg['field'], full_text)

    def _update_chat_display(self):
        """Update the chat display with current conversation history"""
        if not self.chat_service.conversation_history:
            return
        
        # Clear existing messages and rebuild from conversation history
        self._clear_chat_messages()
        
        for message in self.chat_service.conversation_history:
            # Skip system messages in the display (they're used internally)
            if message.role == "system":
                continue
            elif message.role == "user":
                self._add_message_to_chat("You", message.content, "user")
            elif message.role == "assistant":
                self._add_message_to_chat("Assistant", message.content, "assistant")

    def _update_status(self, message: str):
        """Update the connection status"""
        if self.connection_status_field:
            self.connection_status_field.text = message

    async def _test_connection(self):
        """Test connection to Ollama server"""
        self._update_status("Testing connection...")
        try:
            is_connected = await self.chat_service.test_connection()
            if is_connected:
                self._update_status("Connected to Ollama")
            else:
                self._update_status(f"Connection failed to {self.chat_service.host}")
                # Also show in chat
                self._append_to_chat(f"\nConnection failed to {self.chat_service.host}\n")
                self._append_to_chat("Please check:\n")
                self._append_to_chat("1. Ollama is running on the target server\n")
                self._append_to_chat("2. The server allows connections from your IP\n")
                self._append_to_chat("3. No firewall is blocking port 11434\n\n")
        except Exception as e:
            error_msg = f"Connection error: {str(e)}"
            self._update_status(error_msg)
            self._append_to_chat(f"\nConnection error: {str(e)}\n\n")

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
                    self._append_to_chat(f"Loaded {len(models)} models from Ollama server\n\n")
                else:
                    self._append_to_chat(f"Using fallback models. Check connection to load actual models.\n\n")
        except Exception as e:
            error_msg = f"Error loading models: {str(e)}"
            self._append_to_chat(f"\n{error_msg}\n\n")
