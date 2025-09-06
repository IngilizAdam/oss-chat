# OSS Chat Configuration Examples

This file contains configuration examples for different Ollama setups.

## Remote Ollama Server (Recommended for Isaac Sim)
- Host: `http://192.168.1.11:11500` (or your server IP and port)
- Ensure firewall allows connections on port 11500
- This is often the preferred setup for Isaac Sim workstations

## Local Ollama
- Host: `http://localhost:11500`
- Models: Install with `ollama pull <model_name>`

## Custom Port
- Host: `http://192.168.1.11:8080`
- Start Ollama with: `OLLAMA_HOST=0.0.0.0:8080 ollama serve`

## Setting up Ollama for Remote Access

To make Ollama accessible from other machines (like Isaac Sim workstations):

### On the Ollama Server (192.168.1.11):

1. **Configure Ollama to accept external connections:**
   ```bash
   # Set environment variable to bind to all interfaces
   export OLLAMA_HOST=0.0.0.0:11500
   
   # Then start Ollama
   ollama serve
   ```

2. **Or permanently set it:**
   ```bash
   # Add to ~/.bashrc or ~/.profile
   echo 'export OLLAMA_HOST=0.0.0.0:11500' >> ~/.bashrc
   source ~/.bashrc
   ollama serve
   ```

3. **For systemd service (Linux):**
   ```bash
   # Edit the service file
   sudo systemctl edit ollama
   
   # Add this content:
   [Service]
   Environment="OLLAMA_HOST=0.0.0.0:11500"
   
   # Restart service
   sudo systemctl restart ollama
   ```

4. **Configure firewall:**
   ```bash
   # Ubuntu/Debian
   sudo ufw allow 11500/tcp
   
   # CentOS/RHEL
   sudo firewall-cmd --permanent --add-port=11500/tcp
   sudo firewall-cmd --reload
   ```

### Testing Remote Connection

From the Isaac Sim machine, test the connection:
```bash
curl http://192.168.1.11:11500/api/tags
```

You should see JSON output with available models.

## Recommended Models

### Small/Fast Models (Good for testing)
```bash
ollama pull llama3.2:1b
ollama pull mistral:7b-instruct
```

### Medium Models (Balanced)
```bash
ollama pull llama3.2
ollama pull mistral
ollama pull codellama
```

### Large Models (High quality, slower)
```bash
ollama pull llama3.1:8b
ollama pull llama3.1:70b
```

## Environment Variables

You can set these environment variables before starting Ollama:

```bash
# Change host and port
export OLLAMA_HOST=0.0.0.0:11434

# Set GPU layers (for CUDA)
export OLLAMA_NUM_GPU_LAYERS=35

# Set model directory
export OLLAMA_MODELS=/path/to/models
```

## Docker Setup

If you prefer running Ollama in Docker:

```bash
docker run -d -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama
docker exec -it ollama ollama pull llama3.2
```

Then use host: `http://localhost:11434` in the extension.
