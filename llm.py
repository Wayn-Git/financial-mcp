import os
import json
import requests
from typing import List, Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq


# =====================================================
# CONFIG
# =====================================================

MCP_BASE_URL = os.getenv("MCP_BASE_URL", "https://financial-mcp.onrender.com")
MODEL = "llama-3.3-70b-versatile"

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))


# =====================================================
# FASTAPI APP
# =====================================================

app = FastAPI(
    title="Financial LLM Controller",
    description="LLM + MCP tools + memory",
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


# =====================================================
# MEMORY (in-memory, session scoped)
# =====================================================

CONVERSATION_MEMORY: Dict[str, List[Dict[str, str]]] = {}
MAX_MEMORY_LENGTH = 10

def get_memory(session_id: str):
    return CONVERSATION_MEMORY.get(session_id, [])

def update_memory(session_id: str, role: str, content: str):
    CONVERSATION_MEMORY.setdefault(session_id, []).append({
        "role": role,
        "content": content
    })
    CONVERSATION_MEMORY[session_id] = CONVERSATION_MEMORY[session_id][-MAX_MEMORY_LENGTH:]


# =====================================================
# REQUEST / RESPONSE MODELS
# =====================================================

class QuestionRequest(BaseModel):
    question: str
    session_id: str

class AnswerResponse(BaseModel):
    answer: str
    used_tools: List[str]
    symbols: List[str]


# =====================================================
# MCP TOOL CALLS
# =====================================================

def call_price(symbol: str):
    return requests.get(f"{MCP_BASE_URL}/price/{symbol}", timeout=30).json()

def call_fundamentals(symbol: str):
    return requests.get(f"{MCP_BASE_URL}/fundamentals/{symbol}", timeout=30).json()

def call_trend(symbol: str):
    return requests.get(f"{MCP_BASE_URL}/ml/trend/{symbol}", timeout=30).json()

def call_volatility(symbol: str):
    return requests.get(f"{MCP_BASE_URL}/ml/volatility/{symbol}", timeout=30).json()

TOOL_REGISTRY = {
    "get_current_price": call_price,
    "get_fundamentals": call_fundamentals,
    "predict_price_trend": call_trend,
    "predict_volatility": call_volatility,
}


# =====================================================
# SAFE MCP CALL (no crashes)
# =====================================================

def safe_mcp_call(fn, symbol: str):
    try:
        return fn(symbol)
    except requests.exceptions.Timeout:
        return {
            "error": "MCP_TIMEOUT",
            "message": "Data service is waking up. Please try again."
        }
    except requests.exceptions.RequestException as e:
        return {
            "error": "MCP_ERROR",
            "message": str(e)
        }


# =====================================================
# SYMBOL EXTRACTION
# =====================================================

KNOWN_SYMBOLS = {
    "APPLE": "AAPL",
    "MICROSOFT": "MSFT",
    "TESLA": "TSLA",
    "NVIDIA": "NVDA",
    "GOOGLE": "GOOGL",
    "META": "META",
    "AMAZON": "AMZN",
    "VISA": "V",
    "JPMORGAN": "JPM",
}

def extract_symbols(question: str):
    q = question.upper()
    return [sym for name, sym in KNOWN_SYMBOLS.items() if name in q]


# =====================================================
# HARD RULES (CODE > PROMPTS)
# =====================================================

def is_price_question(q: str):
    q = q.lower()
    return any(p in q for p in [
        "current price",
        "stock price",
        "share price",
        "price of",
        "trading at"
    ])

def is_comparison_question(q: str):
    q = q.lower()
    return any(p in q for p in ["vs", "compare", "comparison", "difference"])

def is_risk_question(q: str):
    q = q.lower()
    return any(p in q for p in ["risk", "risky", "volatile"])

def is_trend_question(q: str):
    q = q.lower()
    return any(p in q for p in ["trend", "direction", "moving"])


# =====================================================
# INTENT PROMPT (SOFT GUIDANCE ONLY)
# =====================================================

INTENT_PROMPT = """
You are routing user questions for a financial system.

Decide whether tools are required.
Return JSON only.

{
  "action": "call_tool" | "chat",
  "tool": "get_current_price" | "get_fundamentals" | "predict_price_trend" | "predict_volatility" | null
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
    try:
        return json.loads(completion.choices[0].message.content)
    except Exception:
        return {"action": "chat", "tool": None}


# =====================================================
# SYSTEM PROMPTS
# =====================================================

CHAT_SYSTEM_PROMPT = (
    "You are a calm financial assistant. "
    "Answer conceptually. Do not invent live data."
)

ANALYSIS_SYSTEM_PROMPT = (
    "You are a financial analyst. "
    "Base answers ONLY on tool data. "
    "If data is missing, say so clearly."
)


# =====================================================
# MAIN ENDPOINT
# =====================================================

@app.post("/ask", response_model=AnswerResponse)
def ask_llm(payload: QuestionRequest):
    question = payload.question
    session_id = payload.session_id

    memory = get_memory(session_id)
    symbols = extract_symbols(question)
    decision = decide_action(question)

    # ---------- HARD ENFORCEMENT ----------
    if is_price_question(question) and symbols:
        decision = {"action": "call_tool", "tool": "get_current_price"}

    elif is_comparison_question(question) and len(symbols) >= 2:
        decision = {"action": "call_tool", "tool": "get_fundamentals"}

    elif is_risk_question(question) and symbols:
        decision = {"action": "call_tool", "tool": "predict_volatility"}

    elif is_trend_question(question) and symbols:
        decision = {"action": "call_tool", "tool": "predict_price_trend"}

    # ---------- CHAT MODE ----------
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

        return {"answer": answer, "used_tools": [], "symbols": []}

    # ---------- TOOL MODE ----------
    tool = decision["tool"]
    results = {sym: safe_mcp_call(TOOL_REGISTRY[tool], sym) for sym in symbols}

    messages = [
        {"role": "system", "content": ANALYSIS_SYSTEM_PROMPT},
        *memory,
        {
            "role": "user",
            "content": f"""
Question:
{question}

Tool:
{tool}

Data:
{results}

Answer clearly.
"""
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
