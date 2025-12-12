# AI Literacy Assistant

A chatbot that helps people understand artificial intelligence, recognize AI-generated content, and think critically about AI technology.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/)
- An API key for an OpenAI-compatible LLM endpoint

## Features

- Real-time streaming responses via WebSocket
- Markdown rendering with tables, lists, and code formatting
- Works with any OpenAI-compatible API (OpenAI, Ollama, vLLM, LocalAI, etc.)
- Docker Compose deployment with subdirectory support
- Responsive UI with dark theme

## Quick Start

### 1. Clone and configure

```bash
git clone <your-repo-url>
cd ai-literacy-assistant

# Copy environment template
cp .env.example .env

# Edit .env with your API key and settings
```

### 2. Run with Docker Compose

```bash
docker compose up --build
```

Open http://localhost:3000

## Configuration

All configuration is done via environment variables in `.env`:

| Variable | Description | Default |
|----------|-------------|---------|
| `LOCAL_LLM_API_KEY` | Your API key | (required) |
| `LLM_BASE_URL` | OpenAI-compatible API endpoint | `https://api.openai.com/v1` |
| `LLM_MODEL` | Model to use | `gpt-4o-mini` |
| `BASE_PATH` | Subdirectory path (e.g., `/chatbot`) | (empty) |
| `NEXT_PUBLIC_WS_URL` | WebSocket URL for frontend | `ws://localhost:8000` |
| `ALLOWED_ORIGINS` | CORS origins (comma-separated) | `http://localhost:3000` |

### Example: Using Ollama (local)

```env
LLM_BASE_URL=http://localhost:11434/v1
LLM_MODEL=llama3
LOCAL_LLM_API_KEY=ollama
```

### Example: Subdirectory deployment

To deploy at `https://example.com/chatbot`:

```env
BASE_PATH=/chatbot
NEXT_PUBLIC_BASE_PATH=/chatbot
NEXT_PUBLIC_WS_URL=wss://example.com
ALLOWED_ORIGINS=https://example.com
```

The WebSocket URL is constructed as: `{NEXT_PUBLIC_WS_URL}{NEXT_PUBLIC_BASE_PATH}/ws/chat`
→ Result: `wss://example.com/chatbot/ws/chat`

## Deployment with Nginx

Example nginx configuration for subdirectory deployment:

```nginx
# Frontend (Next.js)
location /chatbot {
    proxy_pass http://localhost:3000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection 'upgrade';
    proxy_set_header Host $host;
    proxy_cache_bypass $http_upgrade;
}

# Backend WebSocket (only endpoint used by frontend)
location /chatbot/ws/chat {
    proxy_pass http://localhost:8000/chatbot/ws/chat;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection 'upgrade';
    proxy_set_header Host $host;
    proxy_read_timeout 86400;
}
```

Note: The backend only exposes a WebSocket endpoint (`/ws/chat`) for chat and an HTTP health check (`/api/health`) used internally by Docker.

## Project Structure

```text
.
├── docker-compose.yml
├── .env.example
├── backend/
│   ├── Dockerfile
│   ├── main.py          # FastAPI + WebSocket server
│   └── requirements.txt
└── frontend/
    ├── Dockerfile
    ├── next.config.ts
    └── src/app/
        ├── page.tsx     # Main chat UI
        ├── layout.tsx
        └── globals.css
```

## Development

### Backend (Python/FastAPI)

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend (Next.js)

```bash
cd frontend
npm install
npm run dev
```

## Tech Stack

- **Frontend**: Next.js 16, React 19, Tailwind CSS, react-markdown
- **Backend**: FastAPI, uvicorn, httpx
- **Deployment**: Docker, Docker Compose

## License

MIT
