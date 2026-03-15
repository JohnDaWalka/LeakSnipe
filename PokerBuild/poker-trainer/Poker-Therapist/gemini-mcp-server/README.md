# Gemini MCP Server

MCP (Model Context Protocol) server that provides access to Google Gemini and Gemma models for GitHub Copilot CLI and mobile app.

## Features

- ✅ **Multiple Gemini Models**: Gemini 2.0 Flash, Gemini 1.5 Pro, Flash, and Flash-8B
- ✅ **Flexible Authentication**: Supports both API keys and Application Default Credentials
- ✅ **GitHub Copilot Integration**: Works with CLI and iPhone app
- ✅ **MCP Tools & Prompts**: Ask questions, explain code, generate code

## Quick Start

### 1. Get a Google AI API Key (Easiest)

1. Visit https://aistudio.google.com/apikey
2. Create an API key
3. Copy `.env.example` to `.env`
4. Add your API key:
   ```
   GOOGLE_API_KEY=your-api-key-here
   ```

### 2. Or Use Existing Google Cloud Credentials

The server is already configured to use your existing credentials at:
`C:\Users\mfane\AppData\Roaming\gcloud\application_default_credentials.json`

Just make sure the Generative Language API is enabled in your project.

### 3. Configure GitHub Copilot CLI

Add this to your GitHub Copilot config file.

**Windows**: `%APPDATA%\github-copilot\config.json`  
**Mac/Linux**: `~/.config/github-copilot/config.json`

```json
{
  "mcpServers": {
    "gemini": {
      "command": "node",
      "args": ["C:\\Users\\mfane\\gemini-mcp-server\\src\\index.js"],
      "env": {
        "GOOGLE_APPLICATION_CREDENTIALS": "C:\\Users\\mfane\\AppData\\Roaming\\gcloud\\application_default_credentials.json"
      }
    }
  }
}
```

Or if using API key:

```json
{
  "mcpServers": {
    "gemini": {
      "command": "node",
      "args": ["C:\\Users\\mfane\\gemini-mcp-server\\src\\index.js"],
      "env": {
        "GOOGLE_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

### 4. Restart GitHub Copilot CLI

Close and reopen your terminal, then test:

```bash
gh copilot --help
```

## Usage

Once configured, you can use Gemini models through the MCP tools:

- **Ask questions**: The `ask_gemini` tool will be available
- **Explain code**: Use the explain-code prompt
- **Generate code**: Use the generate-code prompt

Example (within GitHub Copilot):
```
Ask Gemini to explain this code: [paste code]
```

## iPhone Setup

1. Install GitHub Copilot mobile app from App Store
2. Sign in with the same GitHub account
3. The MCP server configuration syncs automatically
4. **Note**: The server must be running on your PC for mobile access

For mobile access without your PC running, consider deploying the server to a cloud service.

## Available Models

- `gemini-2.0-flash-exp` (default) - Latest experimental model
- `gemini-1.5-pro` - Most capable model
- `gemini-1.5-flash` - Fast and efficient
- `gemini-1.5-flash-8b` - Smallest and fastest

## Troubleshooting

### Authentication Errors

If you see authentication errors:

1. **Using API Key**: Get one from https://aistudio.google.com/apikey
2. **Using ADC**: Run `gcloud auth application-default login`
3. **Enable API**: Visit https://console.cloud.google.com/apis/library/generativelanguage.googleapis.com

### Server Not Connecting

1. Check the config file path is correct
2. Make sure Node.js v18+ is installed: `node --version`
3. Check logs in GitHub Copilot CLI

### Test the Server Directly

```bash
cd gemini-mcp-server
node src/index.js
```

You should see: `[Gemini MCP] Server running on stdio`

## Development

```bash
# Install dependencies
npm install

# Run server
npm start

# Run with auto-reload
npm run dev
```

## License

MIT
