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

import os

EXTENSION_TITLE = "OSS Chat"

EXTENSION_DESCRIPTION = "Chat with LLM models through Ollama from Isaac Sim."

# Default Ollama configuration
DEFAULT_OLLAMA_HOST = "http://192.168.1.11:11500"
DEFAULT_MODEL = "llama3.2"

# System prompt - loaded from file
def load_system_prompt():
    """Load system prompt from system_prompt.txt file"""
    try:
        # Get the directory containing this file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Go up one level to the extension root directory
        extension_root = os.path.dirname(current_dir)
        # Path to system_prompt.txt
        prompt_file = os.path.join(extension_root, "system_prompt.txt")
        
        if os.path.exists(prompt_file):
            with open(prompt_file, 'r', encoding='utf-8') as f:
                return f.read().strip()
        else:
            # Fallback system prompt if file doesn't exist
            return "You are a helpful AI assistant integrated into NVIDIA Isaac Sim."
    except Exception as e:
        print(f"Error loading system prompt: {e}")
        # Fallback system prompt if there's an error
        return "You are a helpful AI assistant integrated into NVIDIA Isaac Sim."

# Load the system prompt from file
SYSTEM_PROMPT = load_system_prompt()
