## System Overview (Mental Model)

 #### Roles clearly separated:

  - Yahoo Finance → Raw financial & price data

  - MCP Server → Fetches data + runs ML models

  - ML Models → Forecast, volatility, anomaly, scoring

  - LLM → Analyst brain (reasoning, comparison, explanation)

 The LLM NEVER touches Yahoo Finance directly. <br>
 It only talks to MCP functions.

## Data Being Pulled From Yahoo Finance

1. Price & Market Data
- Current Price
- Open High low Close
- Volume
- Adjusted Close

2. Historical Data
- Daily Candles
- Weekly Candles
- Monthly Candles

3. Company Fundamentals 
- Market Cap 
- PE ratio
- EPS
- Revenue
- Debt 
- Profit Margin