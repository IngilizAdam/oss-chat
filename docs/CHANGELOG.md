# Changelog

## [1.0.2] - 2025-09-07
### Changed
- System prompt is now loaded from `system_prompt.txt` file instead of being hardcoded
- Improved system prompt flexibility and editability

### Added
- `system_prompt.txt` file for easy system prompt customization
- File-based system prompt loading with error handling and fallback

## [1.0.1] - 2025-01-21
### Changed
- Completely redesigned as a chat interface for LLM interaction
- Added Ollama integration for local AI models
- Created modern chat UI with conversation history
- Added model selection and connection management
- Updated extension metadata and documentation

### Added
- `chat_service.py`: Ollama communication service
- Chat interface with message history
- Model dropdown with auto-population from Ollama
- Connection testing and status indicators
- Conversation management (clear, history preservation)
- Comprehensive README with setup instructions

### Technical Details
- Uses urllib for HTTP requests (Isaac Sim compatible)
- Threaded message processing to prevent UI blocking
- Async connection testing and model loading
- Proper error handling and user feedback

## [0.1.0] - 2025-09-06

### Added
- Initial extension template structure

- Initial version of oss-chat Extension
