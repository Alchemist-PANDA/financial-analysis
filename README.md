# 🤖 Financial Snapshot Agent

A beginner-friendly AI agent that takes raw company financials, calculates key financial metrics, and uses an LLM to generate a professional analyst-style report — all driven by a **LangGraph** pipeline.

---

## 📌 What It Does

```
Raw Company Data  →  Calculate Metrics  →  AI Analysis  →  Printed Report
```

Given a company's revenue, EBITDA, debt, and cash, the agent:
1. Computes financial ratios (margins, net debt, leverage)
2. Sends the data to an AI model
3. Gets back a structured analyst report (profitability, risk, growth, summary)

---

## 🗂️ Project Structure

```
my_agent/
├── .env                  ← Your secret API key (never share this!)
├── .env.example          ← Safe template — copy this to create .env
├── .gitignore            ← Stops .env from being uploaded to GitHub
├── config.py             ← Central settings (model name, tokens, etc.)
├── requirements.txt      ← All Python packages needed
└── app/
    ├── __init__.py       ← Makes `app` a Python package
    ├── agent.py          ← Calls the AI API and returns the analysis
    ├── calculator.py     ← Pure Python math — computes financial ratios
    ├── graph.py          ← LangGraph pipeline (controls execution order)
    ├── main.py           ← Run this file to start the agent
    ├── sample_data.py    ← Example company data (your input)
    └── state.py          ← Shared data container passed through the graph
```

---

## ⚙️ Setup (Step by Step)

### 1. Clone or download the project
```bash
# If using git
git clone <your-repo-url>
cd my_agent
```

### 2. Create a virtual environment (recommended)
```bash
python -m venv venv
venv\Scripts\activate        # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up your API key

Copy the example env file:
```bash
copy .env.example .env
```

Then open `.env` and replace `your-api-key-here` with your real key.

#### 🆓 Free API Key Options (No credit card needed!)
| Provider | Free Tier | Get Key |
|----------|-----------|---------|
| Google Gemini | ✅ Very generous | https://aistudio.google.com/apikey |
| Groq | ✅ Fast & free | https://console.groq.com |
| OpenRouter | ✅ Multiple free models | https://openrouter.ai |
| OpenAI | ⚠️ Paid (small credits for new accounts) | https://platform.openai.com/api-keys |

### 5. Run the agent
```bash
cd app
python main.py
```

---

## 📊 Sample Output

```
════════════════════════════════════════════
  FINANCIAL SNAPSHOT: APEX TECHNOLOGIES
════════════════════════════════════════════

──── CALCULATED METRICS ─────────────────────
  EBITDA Margin      : 12.0%
  Net Margin         : 4.0%
  Net Debt           : $25.0M
  Net Debt / EBITDA  : 2.08x
  Revenue Growth     : 25.0%

──── PROFITABILITY ──────────────────────────
  Apex Technologies demonstrates modest profitability...

──── LEVERAGE & RISK ────────────────────────
  With a Net Debt/EBITDA of 2.08x, leverage is manageable...

──── GROWTH SIGNAL ──────────────────────────
  25% revenue growth signals strong market momentum...

──── ANALYST SUMMARY ────────────────────────
  Apex Technologies is a high-growth company with...
════════════════════════════════════════════
```

---

## 🔧 Customizing the Agent

### Change the company being analyzed
Edit `app/sample_data.py`:
```python
SAMPLE_COMPANY = {
    "company_name": "Your Company Name",
    "revenue": 500.0,           # in millions USD
    "revenue_growth_pct": 15.0, # percentage
    "ebitda": 80.0,
    "net_income": 30.0,
    "cash": 50.0,
    "debt": 100.0
}
```

### Change the AI model
Edit `config.py`:
```python
MODEL_NAME = "gpt-4o-mini"      # OpenAI
# MODEL_NAME = "gemini-1.5-flash"  # Gemini (free)
# MODEL_NAME = "llama-3.1-8b-instant"  # Groq (free)
```

---

## 📚 What You Learn From This Project

- ✅ Python functions, dicts, and type hints
- ✅ Calling AI APIs (OpenAI / Gemini / Groq)
- ✅ LangGraph — the #1 AI agent framework
- ✅ Separating concerns (each file has one clear job)
- ✅ Environment variables & secrets management
- ✅ Project structure best practices

---

## 🐛 Common Issues

| Error | Fix |
|-------|-----|
| `AuthenticationError` | Your API key in `.env` is wrong or missing |
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` |
| `JSONDecodeError` | AI returned bad format — try running again |
| `ImportError` | Make sure you run `python main.py` from inside the `app/` folder |
