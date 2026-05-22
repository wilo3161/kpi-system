# Long-Term Memory

## openclaw
- **Configuration Path**: `C:\Users\wilso\.openclaw\openclaw.json`
- **Global npm module folder**: `C:\Users\wilso\AppData\Roaming\npm\node_modules\openclaw`
- **Key Files**:
  - `dist/pi-embedded-ydXicp1O.js` contains the runner and failover engine logic.
- **Failover Logic (Silent Bot Fix)**:
  - By default, if the bot encounters a rate limit (HTTP 429) or billing error (HTTP 402), it immediately suspends the chat session to protect resources.
  - The engine's suspension logic in `dist/pi-embedded-ydXicp1O.js` was modified to only suspend when no fallback models are configured.
- **Model Setup**:
  - The bot uses a **single direct connection to the DeepSeek API** (`deepseek/deepseek-chat`).
  - Legacy models from OpenRouter and Ollama have been completely removed from the configuration.
  - API Key: Configured via the `DEEPSEEK_API_KEY` variable under `"env"` inside `openclaw.json`.
  - Backup Models: None (direct connection only, as requested).

