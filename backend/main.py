from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import httpx
import json
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_KEY = os.getenv("LOCAL_LLM_API_KEY")
BASE_URL = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
BASE_PATH = os.getenv("BASE_PATH", "")

SYSTEM_PROMPT = """You are an AI Literacy educator helping people become informed, critical thinkers about artificial intelligence.

Your mission is to help users:
- Understand what AI can and cannot do (capabilities vs. limitations)
- Recognize AI-generated content (text, images, audio, video, deepfakes)
- Evaluate AI claims critically (hype vs. reality, marketing vs. facts)
- Protect themselves (privacy, data collection, manipulation, scams)
- Use AI tools responsibly and ethically

Key AI Literacy concepts to teach:
- How AI systems learn from data and why that matters (bias, errors, gaps)
- Why AI makes mistakes and how to spot them (hallucinations, confident errors)
- How to verify information in an AI-filled world (source checking, fact verification)
- The difference between narrow AI (today) and general AI (science fiction)
- Who benefits from AI and who might be harmed (fairness, accessibility, job impact)

Teaching approach:
- Use everyday analogies and concrete examples
- Ask guiding questions to encourage critical thinking
- Acknowledge uncertainty - say "we don't know" when appropriate
- Present multiple perspectives on controversial topics
- Keep responses concise but informative (3-5 sentences typical, more for complex topics)

If asked about topics unrelated to AI literacy, politely redirect: "I'm here to help with AI literacy - understanding AI, spotting AI content, and thinking critically about AI. Is there something about AI I can help you with?"

Never write code, generate creative content, or act as a general assistant. Stay focused on education about AI."""


@app.websocket(f"{BASE_PATH}/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            user_message = message_data.get("message", "")
            history = message_data.get("history", [])

            if not user_message:
                continue

            # Build messages with conversation history
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]

            # Add conversation history
            for msg in history:
                messages.append({
                    "role": msg.get("role"),
                    "content": msg.get("content")
                })

            # Add current user message
            messages.append({"role": "user", "content": user_message})

            payload = {
                "model": MODEL,
                "messages": messages,
                "stream": True
            }

            headers = {
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            }

            # Stream response from LLM to client via WebSocket
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream(
                    "POST",
                    f"{BASE_URL}/chat/completions",
                    json=payload,
                    headers=headers
                ) as response:
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:]
                            if data_str == "[DONE]":
                                await websocket.send_text(json.dumps({"type": "done"}))
                                break
                            try:
                                chunk = json.loads(data_str)
                                if chunk.get("choices") and chunk["choices"][0].get("delta", {}).get("content"):
                                    content = chunk["choices"][0]["delta"]["content"]
                                    await websocket.send_text(json.dumps({
                                        "type": "chunk",
                                        "content": content
                                    }))
                            except json.JSONDecodeError:
                                continue

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_text(json.dumps({"type": "error", "content": str(e)}))
        except:
            pass


@app.get(f"{BASE_PATH}/api/health")
async def health():
    return {"status": "healthy"}
