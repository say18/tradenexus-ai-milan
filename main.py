from fastapi import FastAPI, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Optional
from agents.news_agent import get_supplier_news
from agents.risk_agent import calculate_risk_score
from agents.price_agent import get_price_trends
from agents.doc_agent import analyze_document
from agents.scout_agent import find_global_buyers
from agents.outreach_agent import generate_outreach_email
from agents.analytics_agent import generate_daily_briefing
from agents.visual_agent import analyze_factory_image
from agents.market_pulse_agent import run_market_pulse, tomorrow_agent, trend_agent, mega_trend_agent
from agents.cyber_risk_agent import run_cyber_risk_check
from agents.micro_econ_agent import run_micro_econ_analysis
import uvicorn
import os
import json
import shutil

app = FastAPI(title="TradeNexus AI", version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

# In-memory storage
analyzed_suppliers = []
found_leads = []
last_price_data = ""


# ── Request Models ───────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    supplier_name: str
    industry: str = ""
    country: str = ""


class ScoutRequest(BaseModel):
    product: str
    industry: str
    target_region: str = "Europe"
    seller_company: str = "Our Company"


class EmailRequest(BaseModel):
    buyer_company: str
    buyer_country: str
    buyer_type: str
    seller_company: str
    product: str
    industry: str


class MarketPulseRequest(BaseModel):
    commodity: str
    industry: str
    region: str = "Global"
    country: str = "Bangladesh"


class CyberRiskRequest(BaseModel):
    company_name: str
    domain: str = ""


class MicroEconSupplier(BaseModel):
    name: str
    market_share_pct: float = 20.0
    price_per_unit: float = 10.0
    quality_score: float = 7.0
    units_needed: float = 100.0
    lead_time_days: int = 30
    risk_score: float = 50.0


class MicroEconRequest(BaseModel):
    commodity: str
    industry: str
    budget: float
    suppliers: List[MicroEconSupplier]
    country: str = "Bangladesh"


class TrackSupplierRequest(BaseModel):
    name: str
    industry: str = ""
    country: str = ""
    domain: str = ""


# ── Helpers ──────────────────────────────────────────────────

def get_color(score: int) -> str:
    if score <= 25:
        return "green"
    elif score <= 50:
        return "yellow"
    elif score <= 75:
        return "orange"
    else:
        return "red"


def load_tracked_suppliers() -> list:
    tracker_file = "data/tracked_suppliers.json"
    if os.path.exists(tracker_file):
        try:
            with open(tracker_file, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return []


# ── Base Routes ──────────────────────────────────────────────

@app.get("/")
def root():
    html_path = os.path.join("static", "landing.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.get("/app")
def app_page():
    html_path = os.path.join("static", "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.get("/health")
def health():
    return {
        "status": "ok",
        "version": "3.0.0",
        "message": "TradeNexus AI Phase 3 Running!",
        "agents": [
            "news_agent", "risk_agent", "price_agent",
            "doc_agent", "visual_agent", "scout_agent",
            "outreach_agent", "analytics_agent",
            "market_pulse_agent", "cyber_risk_agent", "micro_econ_agent"
        ]
    }


# ── MODULE A: SupplierPulse ──────────────────────────────────

@app.post("/analyze")
def analyze_supplier(req: AnalyzeRequest):
    print(f"\n🔍 Analyzing: {req.supplier_name}")

    news_result = get_supplier_news(req.supplier_name, req.industry)
    risk_result = calculate_risk_score(
        req.supplier_name,
        news_result["news_summary"],
        req.industry
    )
    price_result = get_price_trends(req.industry, req.country)

    global last_price_data
    last_price_data = price_result["price_data"]

    global analyzed_suppliers
    analyzed_suppliers = [s for s in analyzed_suppliers if s["name"] != req.supplier_name]
    analyzed_suppliers.append({
        "name": req.supplier_name,
        "score": risk_result["score"],
        "level": risk_result["level"],
        "industry": req.industry
    })

    # Auto-track for nightly audit
    try:
        os.makedirs("data", exist_ok=True)
        tracked = load_tracked_suppliers()
        names = [s["name"] for s in tracked]
        if req.supplier_name not in names:
            tracked.append({"name": req.supplier_name, "industry": req.industry, "country": req.country})
            with open("data/tracked_suppliers.json", "w") as f:
                json.dump(tracked, f, indent=2)
    except Exception:
        pass

    report = {
        "supplier": req.supplier_name,
        "industry": req.industry,
        "risk_score": risk_result["score"],
        "risk_level": risk_result["level"],
        "risk_color": get_color(risk_result["score"]),
        "risk_summary": risk_result["summary"],
        "risk_factors": risk_result["factors"],
        "recommended_actions": risk_result["actions"],
        "confidence": risk_result["confidence"],
        "news_summary": news_result["news_summary"],
        "price_data": price_result["price_data"],
        "status": "success"
    }

    print(f"✅ Score: {risk_result['score']}/100 ({risk_result['level']})")
    return report


@app.post("/analyze-document")
async def analyze_doc(
    file: UploadFile = File(...),
    supplier_name: str = Form(default="Unknown Supplier")
):
    print(f"\n📄 Analyzing document: {file.filename}")

    os.makedirs("uploads", exist_ok=True)
    upload_path = os.path.join("uploads", file.filename)
    with open(upload_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    result = analyze_document(upload_path, supplier_name)
    os.remove(upload_path)
    return result


@app.post("/analyze-image")
async def analyze_image(
    file: UploadFile = File(...),
    supplier_name: str = Form(default="Unknown Supplier")
):
    print(f"\n📸 Analyzing image for: {supplier_name}")

    os.makedirs("uploads", exist_ok=True)
    ext = file.filename.split('.')[-1]
    upload_path = os.path.join("uploads", f"factory_{supplier_name}.{ext}")
    with open(upload_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    result = analyze_factory_image(upload_path, supplier_name)
    os.remove(upload_path)
    return result


# ── MODULE A (NEW): Cyber Risk ───────────────────────────────

@app.post("/api/cyber-risk")
async def cyber_risk(req: CyberRiskRequest):
    """Supplier-এর cyber risk OSINT দিয়ে check করে।"""
    print(f"\n🔐 Cyber Risk Check: {req.company_name}")
    try:
        result = await run_cyber_risk_check(
            company_name=req.company_name,
            domain=req.domain if req.domain else None
        )
        return result
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ── MODULE B: DealFlow AI ────────────────────────────────────

@app.post("/scout")
def scout_buyers(req: ScoutRequest):
    print(f"\n🔍 Scouting: {req.product} in {req.target_region}")

    result = find_global_buyers(req.product, req.industry, req.target_region)

    global found_leads
    if result["buyers"]:
        found_leads.extend(result["buyers"])
        found_leads = found_leads[-20:]

    print(f"✅ Found {len(result['buyers'])} buyers")
    return result


@app.post("/generate-email")
def generate_email(req: EmailRequest):
    print(f"\n✉️ Generating email for: {req.buyer_company}")
    return generate_outreach_email(
        buyer_company=req.buyer_company,
        buyer_country=req.buyer_country,
        buyer_type=req.buyer_type,
        seller_company=req.seller_company,
        product=req.product,
        industry=req.industry
    )


# ── MODULE C: Analytics ──────────────────────────────────────

@app.get("/dashboard")
def get_dashboard():
    briefing = generate_daily_briefing(
        suppliers=analyzed_suppliers,
        leads=found_leads,
        price_data=last_price_data
    )

    return {
        "suppliers": analyzed_suppliers,
        "leads": found_leads[:5],
        "briefing": briefing["raw_briefing"],
        "parsed_briefing": briefing.get("parsed", {}),
        "stats": {
            "total_suppliers": len(analyzed_suppliers),
            "high_risk": len([s for s in analyzed_suppliers if s["score"] > 50]),
            "total_leads": len(found_leads),
        }
    }


# ── MODULE D: MarketPulse ────────────────────────────────────

@app.post("/api/market-pulse")
async def market_pulse(req: MarketPulseRequest):
    try:
        result = await run_market_pulse(
            commodity=req.commodity,
            industry=req.industry,
            region=req.region,
            country=req.country,
        )
        return result
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/api/market-pulse/tomorrow")
async def market_pulse_tomorrow(req: MarketPulseRequest):
    try:
        result = await tomorrow_agent(req.commodity, req.industry)
        return {"status": "success", "data": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/api/market-pulse/trend")
async def market_pulse_trend(req: MarketPulseRequest):
    try:
        result = await trend_agent(req.industry, req.region)
        return {"status": "success", "data": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/api/market-pulse/mega")
async def market_pulse_mega(req: MarketPulseRequest):
    try:
        result = await mega_trend_agent(req.industry, req.country)
        return {"status": "success", "data": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ── MODULE D (NEW): Micro-Econ ───────────────────────────────

@app.post("/api/micro-econ")
async def micro_econ(req: MicroEconRequest):
    """Microeconomic analysis — HHI + Utility Maximization।"""
    print(f"\n📊 Micro-Econ Analysis: {req.commodity}")
    try:
        suppliers_list = [s.dict() for s in req.suppliers]
        result = await run_micro_econ_analysis(
            commodity=req.commodity,
            industry=req.industry,
            budget=req.budget,
            suppliers=suppliers_list,
            country=req.country
        )
        return result
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ── Nightly Audit Trail ──────────────────────────────────────

@app.get("/api/audit/last")
def get_last_audit():
    """Last nightly audit summary দেখায়।"""
    try:
        if os.path.exists("logs/last_audit_summary.json"):
            with open("logs/last_audit_summary.json", "r") as f:
                return json.load(f)
        return {"status": "no_audit", "message": "No audit run yet. Use /api/audit/run-now to trigger."}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/api/audit/run-now")
async def run_audit_now():
    """Manual audit trigger — hackathon demo-র জন্য।"""
    try:
        import subprocess
        import threading
        def run():
            subprocess.run(["python", "nightly_audit_trail.py"], capture_output=True)
        thread = threading.Thread(target=run, daemon=True)
        thread.start()
        return {
            "status": "started",
            "message": "Audit started in background. Check /api/audit/last in ~60 seconds."
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/api/suppliers/track")
def track_supplier(req: TrackSupplierRequest):
    """Supplier-কে nightly audit-এ add করে।"""
    try:
        os.makedirs("data", exist_ok=True)
        tracker_file = "data/tracked_suppliers.json"
        suppliers = load_tracked_suppliers()
        names = [s["name"] for s in suppliers]
        if req.name not in names:
            suppliers.append(req.dict())
            with open(tracker_file, "w") as f:
                json.dump(suppliers, f, indent=2)
            return {"status": "added", "total_tracked": len(suppliers)}
        return {"status": "already_tracked", "total_tracked": len(suppliers)}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/api/suppliers/tracked")
def get_tracked_suppliers():
    """Tracked suppliers list দেখায়।"""
    return {"suppliers": load_tracked_suppliers()}



@app.get("/guide")
def platform_guide():
    html_path = os.path.join("static", "guide.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)