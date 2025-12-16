import os
import json
import requests
from typing import List, Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq


# =========================
# CONFIG
# =========================

MCP_BASE_URL = os.getenv("MCP_BASE_URL", "https://financial-mcp.onrender.com")
MODEL = "llama-3.3-70b-versatile"

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))


# =========================
# APP
# =========================

app = FastAPI(
    title="LLM Reasoning Layer",
    description="Groq-powered LLM with MCP tool orchestration and memory",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://financial-mcp-vert.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.options("/{path:path}")
def options_handler(path: str):
    return {}




# =========================
# MEMORY (in-memory, per session)
# =========================

CONVERSATION_MEMORY: Dict[str, List[Dict[str, str]]] = {}
MAX_MEMORY_LENGTH = 10


def get_memory(session_id: str):
    return CONVERSATION_MEMORY.get(session_id, [])


def update_memory(session_id: str, role: str, content: str):
    if session_id not in CONVERSATION_MEMORY:
        CONVERSATION_MEMORY[session_id] = []

    CONVERSATION_MEMORY[session_id].append(
        {"role": role, "content": content}
    )

    CONVERSATION_MEMORY[session_id] = CONVERSATION_MEMORY[session_id][
        -MAX_MEMORY_LENGTH:
    ]


# =========================
# REQUEST / RESPONSE MODELS
# =========================

class QuestionRequest(BaseModel):
    question: str
    session_id: str


class AnswerResponse(BaseModel):
    answer: str
    used_tools: List[str]
    symbols: List[str]


# =========================
# MCP TOOL CALLS (RAW)
# =========================

def call_volatility(symbol: str):
    return requests.get(
        f"{MCP_BASE_URL}/ml/volatility/{symbol}", timeout=30
    ).json()


def call_trend(symbol: str):
    return requests.get(
        f"{MCP_BASE_URL}/ml/trend/{symbol}", timeout=30
    ).json()


def call_price(symbol: str):
    return requests.get(
        f"{MCP_BASE_URL}/price/{symbol}", timeout=30
    ).json()


def call_fundamentals(symbol: str):
    return requests.get(
        f"{MCP_BASE_URL}/fundamentals/{symbol}", timeout=30
    ).json()


TOOL_REGISTRY = {
    "predict_volatility": call_volatility,
    "predict_price_trend": call_trend,
    "get_current_price": call_price,
    "get_fundamentals": call_fundamentals,
}


# =========================
# SAFE MCP WRAPPER (CRITICAL)
# =========================

def safe_mcp_call(fn, symbol: str):
    try:
        return fn(symbol)
    except requests.exceptions.Timeout:
        return {
            "error": "MCP_TIMEOUT",
            "message": "Data service took too long to respond (possible cold start)."
        }
    except requests.exceptions.RequestException as e:
        return {
            "error": "MCP_ERROR",
            "message": str(e)
        }


# =========================
# SYMBOL FALLBACK EXTRACTION
# =========================

KNOWN_SYMBOLS = {
    "APPLE": "AAPL",
    "MICROSOFT": "MSFT",
    "TESLA": "TSLA",
    "NVIDIA": "NVDA",
    "GOOGLE": "GOOGL",
    "META": "META",
    "AMAZON": "AMZN",
    "JPMORGAN": "JPM",
    "VISA": "V",
}


def fallback_extract_symbols(question: str):
    found = []
    q = question.upper()
    for name, symbol in KNOWN_SYMBOLS.items():
        if name in q:
            found.append(symbol)
    return found


# =========================
# INTENT PROMPT (ROUTING)
# =========================

INTENT_PROMPT = """
You are an AI controller for a financial analysis system.

STRICT RULES:
- If the question involves real companies AND comparison, financials, price, risk, trend, or performance → tools are REQUIRED.
- Only choose "chat" for greetings or purely conceptual questions.

Guidance:
- "compare", "vs", "difference" → get_fundamentals
- "risk", "risky", "volatile" → predict_volatility
- "trend", "direction" → predict_price_trend
- "price" → get_current_price

Return ONLY valid JSON:

{
  "action": "call_tool" | "chat",
  "tool": "predict_volatility" | "predict_price_trend" | "get_current_price" | "get_fundamentals" | null,
  "symbols": ["AAPL", "MSFT"]
}
"""


def decide_action(question: str):
    completion = groq_client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": INTENT_PROMPT},
            {"role": "user", "content": question},
        ],
    )

    raw = completion.choices[0].message.content.strip()

    try:
        return json.loads(raw)
    except Exception:
        return {
            "action": "chat",
            "tool": None,
            "symbols": [],
        }


# =========================
# SYSTEM PROMPTS
# =========================

CHAT_SYSTEM_PROMPT = (
    "You are a knowledgeable financial assistant. "
    "Answer conversationally and conceptually. "
    "Do not invent specific financial numbers."
)

ANALYSIS_SYSTEM_PROMPT = (
    "You are a financial analyst. "
    "Base conclusions strictly on the provided tool data. "
    "If data is missing or errors occur, say so clearly. "
    "Do not rely on general knowledge."
)


# =========================
# MAIN ENDPOINT
# =========================

@app.post("/ask", response_model=AnswerResponse)
def ask_llm(payload: QuestionRequest):
    question = payload.question
    session_id = payload.session_id

    memory = get_memory(session_id)
    decision = decide_action(question)

    symbols = decision.get("symbols", [])

    # Fallback symbol extraction
    if not symbols:
        symbols = fallback_extract_symbols(question)

    # Force tools for multi-company comparisons
    if len(symbols) >= 2 and decision["action"] == "chat":
        decision["action"] = "call_tool"
        decision["tool"] = "get_fundamentals"

    # -------------------------
    # CHAT MODE
    # -------------------------
    if decision["action"] == "chat":
        messages = [
            {"role": "system", "content": CHAT_SYSTEM_PROMPT},
            *memory,
            {"role": "user", "content": question},
        ]

        completion = groq_client.chat.completions.create(
            model=MODEL,
            messages=messages,
        )

        answer = completion.choices[0].message.content

        update_memory(session_id, "user", question)
        update_memory(session_id, "assistant", answer)

        return {
            "answer": answer,
            "used_tools": [],
            "symbols": [],
        }

    # -------------------------
    # TOOL MODE
    # -------------------------
    tool = decision["tool"]
    results = {}

    for sym in symbols:
        results[sym] = safe_mcp_call(TOOL_REGISTRY[tool], sym)

    messages = [
        {"role": "system", "content": ANALYSIS_SYSTEM_PROMPT},
        *memory,
        {
            "role": "user",
            "content": f"""
User question:
{question}

Tool used:
{tool}

Tool results:
{results}

Explain clearly and concisely.
""",
        },
    ]

    completion = groq_client.chat.completions.create(
        model=MODEL,
        messages=messages,
    )

    answer = completion.choices[0].message.content

    update_memory(session_id, "user", question)
    update_memory(session_id, "assistant", answer)

    return {
        "answer": answer,
        "used_tools": [tool],
        "symbols": symbols,
    }
