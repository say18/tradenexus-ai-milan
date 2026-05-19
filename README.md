# TradeNexus AI
### AI-Powered Trade Intelligence Platform
**Milan AI Week Hackathon 2026 — lablab.ai**

🌐 **Live Demo:** http://136.244.101.167:8000  
📁 **GitHub:** https://github.com/say18/tradenexus-ai-milan

---

## 🎯 Use Case

400 million SMEs globally make trade decisions using Google Search and gut feeling. TradeNexus AI gives them enterprise-grade trade intelligence — supplier risk monitoring, global buyer discovery, market prediction, and autonomous nightly audits — all powered by AI.

---

## 🏗️ Architecture

```
TradeNexus AI v3.0
│
├── MODULE A — SupplierPulse (5 Agents)
│   ├── News Agent        → Real-time supplier intelligence (Qwen 2.5 72B)
│   ├── Risk Agent        → Risk score 0-100 (DeepSeek-R1)
│   ├── Doc Agent         → PDF financial analysis (Qwen 2.5 72B)
│   ├── Visual Agent      → Factory image analysis (Vision Model)
│   └── Cyber Risk Agent  → Free OSINT security scan
│
├── MODULE B — DealFlow AI (3 Agents)
│   ├── Scout Agent       → Global buyer discovery (Qwen 2.5 72B)
│   ├── Qualify Agent     → Buyer fit scoring
│   └── Outreach Agent    → Personalized cold email generation
│
├── MODULE C — Analytics Dashboard
│   └── Analytics Agent   → AI daily briefing (Qwen 2.5 72B)
│
├── MODULE D — MarketPulse AI (4 Agents)
│   ├── Tomorrow Agent    → 24-48hr price prediction (DeepSeek-R1)
│   ├── Trend Agent       → 1-5 year industry forecast (Qwen 2.5 72B)
│   ├── Mega Trend Agent  → 5-10 year disruption analysis (Mistral Large)
│   └── Micro-Econ Agent  → HHI + Utility Maximization (DeepSeek-R1)
│
└── AUTONOMOUS SYSTEM
    └── Nightly Audit Trail → Vultr Cron (midnight, zero human input)
```

---

## 🤖 AI Models (Benchmarked on 600+ prompts)

| Task | Model | Why Selected |
|---|---|---|
| Risk reasoning | DeepSeek-R1 | Superior logical/economic calculations |
| Market analysis | Qwen 2.5 72B | Best structured JSON output |
| Long-term trends | Mistral Large | Strong multi-step strategic reasoning |
| Vision analysis | Qwen 2.5 VL | Multimodal with fallback chain |

---

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| Backend | FastAPI (Python 3.11) |
| AI Models | Featherless AI |
| Market Data | Kraken Public API |
| OSINT | crt.sh, urlscan.io, HaveIBeenPwned |
| Deployment | Vultr VM (Ubuntu 22.04, Amsterdam) |
| Scheduler | Vultr Cron (nightly autonomous audit) |
| Frontend | HTML/CSS/JS |

---

## 🚀 Setup & Installation

```bash
# Clone repository
git clone https://github.com/say18/tradenexus-ai-milan.git
cd tradenexus-ai-milan

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install fastapi uvicorn python-dotenv openai httpx pypdf PyPDF2 python-multipart

# Create .env file
echo "FEATHERLESS_API_KEY=your_key_here" > .env
echo "API_BASE_URL=http://localhost:8000" >> .env

# Create required directories
mkdir -p uploads data logs static

# Run server
uvicorn main:app --host 0.0.0.0 --port 8000
```

Open `http://localhost:8000` in browser.

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Landing page |
| GET | `/app` | Main platform |
| GET | `/guide` | Platform guide |
| POST | `/analyze` | Supplier risk analysis |
| POST | `/analyze-document` | PDF document analysis |
| POST | `/analyze-image` | Factory image analysis |
| POST | `/api/cyber-risk` | OSINT cyber security scan |
| POST | `/scout` | Global buyer discovery |
| POST | `/generate-email` | Outreach email generation |
| GET | `/dashboard` | Analytics dashboard |
| POST | `/api/market-pulse` | Full market prediction |
| POST | `/api/micro-econ` | HHI + Utility Maximization |
| GET | `/api/audit/last` | Last nightly audit results |
| POST | `/api/audit/run-now` | Manual audit trigger |

---

## 🌙 Autonomous Nightly Audit

```bash
# Vultr Cron — runs every night at midnight UTC
0 0 * * * cd /home/tradenexus && /home/tradenexus/venv/bin/python nightly_audit_trail.py >> logs/audit.log 2>&1
```

Zero human input required. Automatically re-checks all tracked suppliers for risk and cyber threats.

---

## 🏆 Sponsors

- **Featherless AI** — LLM inference (DeepSeek-R1, Qwen 2.5 72B, Mistral Large)
- **Kraken** — Real-time market data
- **Vultr** — VM deployment + Cron scheduler

---

## 📊 Key Metrics

- 11 autonomous AI agents
- 9 platform modules
- 100% autonomous nightly monitoring
- Free OSINT — no paid API keys for security scanning
- 600+ prompts benchmarked for model selection
