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

EXTENSION_TITLE = "OSS Chat"

EXTENSION_DESCRIPTION = "Chat with LLM models through Ollama from Isaac Sim."

# Default Ollama configuration
DEFAULT_OLLAMA_HOST = "http://192.168.1.11:11500"
DEFAULT_MODEL = "llama3.2"

# System prompt - hardcoded for all conversations
SYSTEM_PROMPT = """You are a helpful AI assistant integrated into NVIDIA Isaac Sim, a robotics simulation platform. You are knowledgeable about:

- Robotics and autonomous systems
- 3D simulation and physics
- NVIDIA Omniverse and Isaac Sim
- Python programming for robotics
- USD (Universal Scene Description)
- Computer vision and AI for robotics
- ROS (Robot Operating System)
- Simulation best practices

You provide clear, practical advice and can help with both technical implementation and conceptual understanding. Keep responses concise but informative, and always consider the robotics simulation context when relevant."""
