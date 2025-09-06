# OSS Chat Extension

A chat interface extension for Isaac Sim that allows you to interact with Large Language Models through Ollama.

## Features

- **Chat Interface**: Clean, intuitive chat UI integrated into Isaac Sim
- **Ollama Integration**: Connect to local or remote Ollama instances
- **Model Selection**: Choose from available models in your Ollama instance
- **Conversation History**: Maintains chat history during your session
- **Connection Management**: Easy configuration and connection testing

## Prerequisites

1. **Isaac Sim**: This extension requires Isaac Sim to be installed
2. **Ollama**: Install and run Ollama on your machine or accessible server
   - Download from: https://ollama.ai/
   - Install models you want to use (e.g., `ollama pull llama3.2`)

## Installation

1. Clone or place this extension in your Isaac Sim extensions directory
2. Enable the extension in Isaac Sim's Extension Manager
3. The "OSS Chat" menu item will appear in the toolbar

Alternatively, run Isaac Sim with the flags:
```bash
--ext-folder {path_to_ext_folder} --enable {ext_directory_name}
```

## Usage

### Setting up Ollama

1. Install Ollama from https://ollama.ai/
2. Pull some models:
   ```bash
   ollama pull llama3.2
   ollama pull llama2
   ollama pull mistral
   ```
3. Start Ollama (if not running as a service):
   ```bash
   ollama serve
   ```

### Using the Extension

1. Open Isaac Sim and enable the OSS Chat extension
2. Click on "OSS Chat" in the toolbar to open the interface
3. Configure connection settings:
   - Set the Ollama host URL (default: http://localhost:11434)
   - Test the connection to ensure it's working
4. Select a model from the dropdown
5. Start chatting!

### Interface Components

- **Connection Settings**: Configure Ollama server URL and test connectivity
- **Model Selection**: Choose from available models
- **Chat**: Main conversation area with history
- **Controls**: Send messages and clear chat history

## Configuration

### Default Settings

- **Ollama Host**: `http://localhost:11434`
- **Default Model**: `llama3.2`

You can modify these defaults in `global_variables.py`.

### Custom Ollama Setup

If you're running Ollama on a different host or port:

1. Open the "Connection Settings" frame in the UI
2. Update the Ollama Host field (e.g., `http://192.168.1.100:11434`)
3. Click "Test Connection" to verify

## Architecture

The extension consists of several key components:

- `extension.py`: Main extension entry point and UI management
- `ui_builder.py`: Chat interface construction and event handling
- `chat_service.py`: Ollama communication and conversation management
- `global_variables.py`: Configuration constants

## Troubleshooting

### Connection Issues

1. **"Connection failed"**: 
   - Ensure Ollama is running (`ollama serve`)
   - Check the host URL is correct
   - Verify firewall settings if using remote Ollama

2. **"No models available"**:
   - Pull models using `ollama pull <model_name>`
   - Restart Ollama service

3. **Empty responses**:
   - Check Ollama logs for errors
   - Try a different model
   - Ensure sufficient system resources

### Performance Tips

- Use smaller models (like `llama3.2:1b`) for faster responses
- Ensure adequate RAM and CPU resources
- Close unnecessary applications while chatting

## Development

The extension uses Isaac Sim's UI components and follows the standard extension architecture. Key files:

- Configuration: `config/extension.toml`
- Python module: `oss_chat_python/`
- UI components: Isaac Sim's `isaacsim.gui.components`

## License

Licensed under the Apache License, Version 2.0. See the extension files for full license text.

