import os
import json
import requests
import time
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
# MCP TOOL CALLS WITH RETRY
# =====================================================

def call_price(symbol: str):
    return requests.get(f"{MCP_BASE_URL}/price/{symbol}", timeout=60).json()

def call_fundamentals(symbol: str):
    return requests.get(f"{MCP_BASE_URL}/fundamentals/{symbol}", timeout=60).json()

def call_trend(symbol: str):
    return requests.get(f"{MCP_BASE_URL}/ml/trend/{symbol}", timeout=60).json()

def call_volatility(symbol: str):
    return requests.get(f"{MCP_BASE_URL}/ml/volatility/{symbol}", timeout=60).json()

TOOL_REGISTRY = {
    "get_current_price": call_price,
    "get_fundamentals": call_fundamentals,
    "predict_price_trend": call_trend,
    "predict_volatility": call_volatility,
}


# =====================================================
# SAFE MCP CALL WITH RETRY (handles cold starts)
# =====================================================

def safe_mcp_call(fn, symbol: str, max_retries=2):
    """
    Retries MCP calls to handle Render cold starts.
    First call wakes the server, second usually succeeds.
    """
    for attempt in range(max_retries):
        try:
            result = fn(symbol)
            # Check if result contains error
            if isinstance(result, dict) and "error" in result:
                if attempt < max_retries - 1:
                    time.sleep(3)  # Wait for server to wake up
                    continue
            return result
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                time.sleep(3)
                continue
            return {
                "error": "MCP_TIMEOUT",
                "message": f"The financial data service is starting up. This can take 30-60 seconds on first request. Please try again in a moment."
            }
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                time.sleep(3)
                continue
            return {
                "error": "MCP_ERROR",
                "message": f"Could not reach financial data service: {str(e)}"
            }
    
    return {
        "error": "MCP_RETRY_FAILED",
        "message": "Service is waking up. Please retry your request."
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
    "AAPL": "AAPL",
    "MSFT": "MSFT",
    "TSLA": "TSLA",
    "NVDA": "NVDA",
    "GOOGL": "GOOGL",
    "AMZN": "AMZN",
}

def extract_symbols(question: str):
    q = question.upper()
    found = []
    for name, sym in KNOWN_SYMBOLS.items():
        if name in q and sym not in found:
            found.append(sym)
    return found


# =====================================================
# HARD RULES (CODE > PROMPTS)
# =====================================================

def is_greeting(q: str):
    """Check if message is a greeting or casual chat"""
    q = q.lower().strip()
    greetings = ["hi", "hello", "hey", "good morning", "good afternoon", 
                 "good evening", "howdy", "greetings", "what's up", "sup"]
    return any(q.startswith(g) for g in greetings) or q in greetings

def is_price_question(q: str):
    q = q.lower()
    return any(p in q for p in [
        "current price",
        "stock price",
        "share price",
        "price of",
        "trading at",
        "how much is",
        "what's the price"
    ])

def is_comparison_question(q: str):
    q = q.lower()
    return any(p in q for p in ["vs", "compare", "comparison", "difference", "between"])

def is_risk_question(q: str):
    q = q.lower()
    return any(p in q for p in ["risk", "risky", "volatile", "volatility", "safe", "danger"])

def is_trend_question(q: str):
    q = q.lower()
    return any(p in q for p in ["trend", "direction", "moving", "forecast", "predict", "outlook"])


# =====================================================
# INTENT PROMPT (SOFT GUIDANCE ONLY)
# =====================================================

INTENT_PROMPT = """You are routing user questions for a financial system.

Analyze the user's question and decide if it requires real-time financial data.

Return ONLY valid JSON with this structure:
{
  "action": "call_tool" or "chat",
  "tool": "get_current_price" or "get_fundamentals" or "predict_price_trend" or "predict_volatility" or null
}

Rules:
- Use "chat" for: greetings, general questions, explanations, concepts
- Use "call_tool" only when specific stock data is needed
- If asking about price/value of a stock → "get_current_price"
- If comparing multiple stocks → "get_fundamentals"
- If asking about risk/volatility → "predict_volatility"
- If asking about trend/direction → "predict_price_trend"
"""

def decide_action(question: str):
    """Use LLM for soft intent detection"""
    completion = groq_client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": INTENT_PROMPT},
            {"role": "user", "content": question},
        ],
        temperature=0.1,
    )
    try:
        content = completion.choices[0].message.content.strip()
        # Clean up markdown code blocks if present
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()
        return json.loads(content)
    except Exception as e:
        print(f"Intent parsing error: {e}")
        return {"action": "chat", "tool": None}


# =====================================================
# SYSTEM PROMPTS (IMPROVED)
# =====================================================

CHAT_SYSTEM_PROMPT = """You are a friendly and professional financial assistant.

Your role:
- Answer financial questions conversationally and naturally
- Respond warmly to greetings and casual conversation
- Explain financial concepts clearly without jargon
- If asked about specific stock data, politely indicate you need a stock symbol
- Never fabricate live stock prices, trends, or financial data
- Be concise but helpful

Keep responses natural and human-like."""

ANALYSIS_SYSTEM_PROMPT = """You are a professional financial analyst.

Your role:
- Analyze the provided financial data carefully
- Base ALL answers strictly on the tool data provided
- If data shows an error or is missing, clearly state this to the user
- Present insights in clear, actionable language
- Compare data points when multiple stocks are provided
- Never speculate or invent data

Be precise and fact-based."""


# =====================================================
# MAIN ENDPOINT
# =====================================================

@app.post("/ask", response_model=AnswerResponse)
def ask_llm(payload: QuestionRequest):
    question = payload.question
    session_id = payload.session_id

    memory = get_memory(session_id)
    symbols = extract_symbols(question)
    
    # ---------- HARD ENFORCEMENT ----------
    # Handle greetings immediately
    if is_greeting(question):
        decision = {"action": "chat", "tool": None}
    # Override LLM decision for specific financial queries
    elif is_price_question(question) and symbols:
        decision = {"action": "call_tool", "tool": "get_current_price"}
    elif is_comparison_question(question) and len(symbols) >= 2:
        decision = {"action": "call_tool", "tool": "get_fundamentals"}
    elif is_risk_question(question) and symbols:
        decision = {"action": "call_tool", "tool": "predict_volatility"}
    elif is_trend_question(question) and symbols:
        decision = {"action": "call_tool", "tool": "predict_price_trend"}
    else:
        # Let LLM decide for ambiguous cases
        decision = decide_action(question)

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
            temperature=0.7,
        )

        answer = completion.choices[0].message.content

        update_memory(session_id, "user", question)
        update_memory(session_id, "assistant", answer)

        return {"answer": answer, "used_tools": [], "symbols": []}

    # ---------- TOOL MODE ----------
    tool = decision["tool"]
    results = {}
    
    for sym in symbols:
        results[sym] = safe_mcp_call(TOOL_REGISTRY[tool], sym, max_retries=2)

    # Check if all results are errors
    all_errors = all(
        isinstance(r, dict) and "error" in r 
        for r in results.values()
    )
    
    if all_errors:
        error_msgs = [r.get("message", "Unknown error") for r in results.values()]
        answer = f"I'm having trouble reaching the financial data service right now. {error_msgs[0]} Please try again in a moment."
        
        update_memory(session_id, "user", question)
        update_memory(session_id, "assistant", answer)
        
        return {
            "answer": answer,
            "used_tools": [tool],
            "symbols": symbols,
        }

    messages = [
        {"role": "system", "content": ANALYSIS_SYSTEM_PROMPT},
        *memory,
        {
            "role": "user",
            "content": f"""User Question: {question}

Tool Used: {tool}

Financial Data Retrieved:
{json.dumps(results, indent=2)}

Provide a clear, professional analysis based on this data."""
        },
    ]

    completion = groq_client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0.3,
    )

    answer = completion.choices[0].message.content

    update_memory(session_id, "user", question)
    update_memory(session_id, "assistant", answer)

    return {
        "answer": answer,
        "used_tools": [tool],
        "symbols": symbols,
    }


# =====================================================
# WARMUP ENDPOINT (Call this on frontend load)
# =====================================================

@app.get("/warmup")
def warmup():
    """
    Ping the MCP server to wake it up.
    Call this from your frontend on app load.
    """
    try:
        response = requests.get(f"{MCP_BASE_URL}/", timeout=60)
        return {"status": "MCP server is awake", "response": response.json()}
    except Exception as e:
        return {"status": "MCP server is waking up", "message": str(e)}