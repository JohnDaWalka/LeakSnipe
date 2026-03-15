#!/usr/bin/env node
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { GoogleGenerativeAI } from '@google/generative-ai';
import dotenv from 'dotenv';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { readFileSync } from 'fs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Load environment variables
dotenv.config({ path: join(__dirname, '..', '.env') });

class GeminiMCPServer {
  constructor() {
    this.server = new Server(
      {
        name: 'gemini-mcp-server',
        version: '1.0.0',
      },
      {
        capabilities: {
          prompts: {},
          resources: {},
          tools: {},
        },
      }
    );

    this.genAI = null;
    this.setupHandlers();
  }

  async initialize() {
    try {
      let apiKey = process.env.GOOGLE_API_KEY;

      // If no API key in env, try to use Application Default Credentials
      if (!apiKey && process.env.GOOGLE_APPLICATION_CREDENTIALS) {
        console.error('[Gemini MCP] Attempting to use Application Default Credentials...');
        try {
          const credsPath = process.env.GOOGLE_APPLICATION_CREDENTIALS;
          const creds = JSON.parse(readFileSync(credsPath, 'utf8'));
          
          if (creds.refresh_token) {
            console.error('[Gemini MCP] Found OAuth credentials, but Gemini API requires an API key.');
            console.error('[Gemini MCP] Please get an API key from: https://aistudio.google.com/apikey');
            console.error('[Gemini MCP] Then set GOOGLE_API_KEY in your environment or .env file');
            throw new Error('API key required');
          }
        } catch (err) {
          console.error('[Gemini MCP] Could not read credentials:', err.message);
          throw err;
        }
      }

      if (!apiKey) {
        throw new Error('GOOGLE_API_KEY environment variable is required. Get one from: https://aistudio.google.com/apikey');
      }

      console.error('[Gemini MCP] Initializing with API key...');
      this.genAI = new GoogleGenerativeAI(apiKey);
      console.error('[Gemini MCP] Initialized successfully');
    } catch (error) {
      console.error('[Gemini MCP] Initialization error:', error.message);
      throw error;
    }
  }

  setupHandlers() {
    // List available prompts
    this.server.setRequestHandler('prompts/list', async () => {
      return {
        prompts: [
          {
            name: 'explain-code',
            description: 'Explain code using Gemini',
            arguments: [
              {
                name: 'code',
                description: 'The code to explain',
                required: true,
              },
              {
                name: 'language',
                description: 'Programming language',
                required: false,
              },
            ],
          },
          {
            name: 'generate-code',
            description: 'Generate code using Gemini',
            arguments: [
              {
                name: 'prompt',
                description: 'What to generate',
                required: true,
              },
              {
                name: 'language',
                description: 'Programming language',
                required: false,
              },
            ],
          },
        ],
      };
    });

    // Get specific prompt
    this.server.setRequestHandler('prompts/get', async (request) => {
      const { name, arguments: args } = request.params;

      if (name === 'explain-code') {
        const code = args.code || '';
        const language = args.language || 'unknown';
        return {
          messages: [
            {
              role: 'user',
              content: {
                type: 'text',
                text: `Explain this ${language} code:\n\n${code}`,
              },
            },
          ],
        };
      }

      if (name === 'generate-code') {
        const prompt = args.prompt || '';
        const language = args.language || '';
        return {
          messages: [
            {
              role: 'user',
              content: {
                type: 'text',
                text: `Generate ${language} code for: ${prompt}`,
              },
            },
          ],
        };
      }

      throw new Error(`Unknown prompt: ${name}`);
    });

    // List available tools
    this.server.setRequestHandler('tools/list', async () => {
      return {
        tools: [
          {
            name: 'ask_gemini',
            description: 'Ask Google Gemini a question or request code generation',
            inputSchema: {
              type: 'object',
              properties: {
                prompt: {
                  type: 'string',
                  description: 'The question or request for Gemini',
                },
                model: {
                  type: 'string',
                  description: 'Model to use',
                  enum: [
                    'gemini-2.0-flash-exp',
                    'gemini-1.5-pro',
                    'gemini-1.5-flash',
                    'gemini-1.5-flash-8b',
                  ],
                  default: 'gemini-2.0-flash-exp',
                },
              },
              required: ['prompt'],
            },
          },
        ],
      };
    });

    // Execute tool
    this.server.setRequestHandler('tools/call', async (request) => {
      const { name, arguments: args } = request.params;

      if (name === 'ask_gemini') {
        try {
          const modelName = args.model || 'gemini-2.0-flash-exp';
          const model = this.genAI.getGenerativeModel({ model: modelName });

          const result = await model.generateContent(args.prompt);
          const response = await result.response;
          const text = response.text();

          return {
            content: [
              {
                type: 'text',
                text: text,
              },
            ],
          };
        } catch (error) {
          return {
            content: [
              {
                type: 'text',
                text: `Error: ${error.message}`,
              },
            ],
            isError: true,
          };
        }
      }

      throw new Error(`Unknown tool: ${name}`);
    });
  }

  async run() {
    await this.initialize();
    
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    
    console.error('[Gemini MCP] Server running on stdio');
  }
}

// Start the server
const server = new GeminiMCPServer();
server.run().catch((error) => {
  console.error('[Gemini MCP] Fatal error:', error);
  process.exit(1);
});
