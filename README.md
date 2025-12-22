# FintelAI - AI-Powered Financial Intelligence Platform

## System Architecture
```
User Query → LLM Controller → MCP Server → Yahoo Finance
                ↓                ↓
           Groq LLM        ML Models
                ↓                ↓
           Analysis ← Financial Data
```

### Component Roles

- **Yahoo Finance**: Raw financial & market data source
- **MCP Server**: Data fetching + ML predictions (volatility, trends)
- **LLM Controller**: Query routing, decision logic, conversational analysis
- **Groq LLM**: Financial reasoning, comparison, natural language responses

**The LLM never touches Yahoo Finance directly—only through MCP tools.**

---

## Available Financial Data

### Real-Time Market Data
- Current Price, Open, High, Low, Close
- Volume, Adjusted Close
- Intraday movements

### Historical Data
- Daily, Weekly, Monthly candles
- Configurable periods (1d, 5d, 1mo, 3mo, 1y, max)

### Company Fundamentals
- Market Cap, P/E Ratio, EPS
- Revenue, Debt-to-Equity
- Profit Margins, Dividend Yield

### ML Predictions
- **Price Trend Forecasting**: 7-day LSTM predictions
- **Volatility Analysis**: Risk scoring based on historical volatility
- **Anomaly Detection**: Unusual price movements

---

## MCP Tools

| Tool | Purpose | Returns |
|------|---------|---------|
| `get_current_price` | Live stock price | Price, change %, volume |
| `get_fundamentals` | Company metrics | Market cap, P/E, EPS, debt |
| `predict_price_trend` | 7-day forecast | Predicted prices, confidence |
| `predict_volatility` | Risk assessment | Volatility score, risk level |

---

## Tech Stack

**Frontend**: React, Tailwind CSS, Lucide Icons  
**Backend**: FastAPI (LLM Controller + MCP Server)  
**LLM**: Groq (llama-3.3-70b-versatile)  
**Data**: Yahoo Finance (yfinance)  
**ML**: scikit-learn, LSTM (TensorFlow/Keras)

---

## Key Features

✅ **Smart Query Routing**: Code-enforced rules override LLM for precision  
✅ **Multi-Stock Comparison**: Analyze multiple tickers simultaneously  
✅ **Conversational Memory**: Context-aware responses (10-message history)  
✅ **Cold Start Handling**: Auto-retry logic for Render free tier  
✅ **ML-Powered Insights**: Predictive analytics, not just data retrieval  

---

## Usage Examples

- *"What's Tesla's current price?"* → `get_current_price`
- *"Compare Apple vs Microsoft fundamentals"* → `get_fundamentals`
- *"Is Nvidia risky right now?"* → `predict_volatility`
- *"What's the trend for Amazon?"* → `predict_price_trend`

---

## Deployment

**MCP Server**: Render (https://financial-mcp.onrender.com)  
**LLM Controller**: Render (https://llm-mcp-financial.onrender.com)  
**Frontend**: Vercel (https://financial-mcp-vert.vercel.app)

**Note**: Free tier servers may cold start (30-60s on first request). Frontend includes automatic warmup.