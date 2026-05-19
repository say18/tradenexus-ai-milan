"""
Nightly Audit Trail — TradeNexus AI
====================================
Vultr Cron Scheduler দিয়ে রাত ১২টায় auto-run হয়।
সব suppliers check করে, risk update করে, dashboard-এ save করে।

Vultr Cron Command:
0 0 * * * cd /home/tradenexus && python nightly_audit_trail.py >> logs/audit.log 2>&1
"""

import os
import json
import asyncio
import httpx
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

# TradeNexus API base URL (same server)
API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")

# Audit log file
AUDIT_LOG_FILE = "logs/nightly_audit.json"
AUDIT_SUMMARY_FILE = "logs/last_audit_summary.json"


def log(msg: str):
    """Timestamped log।"""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"[{ts}] {msg}")


def ensure_log_dir():
    os.makedirs("logs", exist_ok=True)


def load_audit_history() -> list:
    """Past audit logs load করে।"""
    try:
        if os.path.exists(AUDIT_LOG_FILE):
            with open(AUDIT_LOG_FILE, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return []


def save_audit_history(history: list):
    """Audit history save করে।"""
    try:
        with open(AUDIT_LOG_FILE, "w") as f:
            json.dump(history[-100:], f, indent=2, default=str)  # Keep last 100 runs
    except Exception as e:
        log(f"❌ Could not save audit history: {e}")


def save_summary(summary: dict):
    """Last audit summary save করে — Dashboard দেখবে।"""
    try:
        with open(AUDIT_SUMMARY_FILE, "w") as f:
            json.dump(summary, f, indent=2, default=str)
    except Exception as e:
        log(f"❌ Could not save summary: {e}")


async def check_supplier_via_api(supplier: dict) -> dict:
    """TradeNexus API দিয়ে supplier re-analyze করে।"""
    try:
        async with httpx.AsyncClient(timeout=60) as c:
            r = await c.post(f"{API_BASE}/analyze", json={
                "supplier_name": supplier["name"],
                "industry": supplier.get("industry", ""),
                "country": supplier.get("country", "")
            })
            if r.status_code == 200:
                return r.json()
    except Exception as e:
        log(f"⚠️  API call failed for {supplier['name']}: {e}")
    return {}


async def cyber_check_via_api(supplier: dict) -> dict:
    """Cyber risk check via API।"""
    try:
        async with httpx.AsyncClient(timeout=60) as c:
            r = await c.post(f"{API_BASE}/api/cyber-risk", json={
                "company_name": supplier["name"],
                "domain": supplier.get("domain", "")
            })
            if r.status_code == 200:
                return r.json()
    except Exception as e:
        log(f"⚠️  Cyber check failed for {supplier['name']}: {e}")
    return {}


def load_tracked_suppliers() -> list:
    """Tracked suppliers load করে।
    Production-এ এটা database থেকে আসবে।
    এখন file-based।
    """
    tracker_file = "data/tracked_suppliers.json"
    if os.path.exists(tracker_file):
        try:
            with open(tracker_file, "r") as f:
                return json.load(f)
        except Exception:
            pass

    # Default test suppliers যদি file না থাকে
    return [
        {"name": "Evergrande", "industry": "real estate", "country": "China"},
        {"name": "TSMC", "industry": "semiconductor", "country": "Taiwan"},
        {"name": "Samsung", "industry": "electronics", "country": "South Korea"},
    ]


def save_tracked_suppliers(suppliers: list):
    """Tracked suppliers save করে।"""
    os.makedirs("data", exist_ok=True)
    try:
        with open("data/tracked_suppliers.json", "w") as f:
            json.dump(suppliers, f, indent=2, default=str)
    except Exception as e:
        log(f"❌ Could not save suppliers: {e}")


async def run_nightly_audit():
    """Main nightly audit function।"""
    ensure_log_dir()
    start_time = datetime.now(timezone.utc)

    log("=" * 60)
    log("🌙 TradeNexus AI — Nightly Audit Trail Started")
    log("=" * 60)

    suppliers = load_tracked_suppliers()
    log(f"📋 Found {len(suppliers)} tracked suppliers")

    audit_results = []
    alerts = []
    high_risk_count = 0
    critical_count = 0

    for i, supplier in enumerate(suppliers, 1):
        name = supplier["name"]
        log(f"\n[{i}/{len(suppliers)}] Checking: {name}")

        result = {
            "supplier": name,
            "industry": supplier.get("industry", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "risk_check": {},
            "cyber_check": {},
            "changes": [],
            "alerts": []
        }

        # Risk analysis
        log(f"  🔍 Risk analysis...")
        risk_data = await check_supplier_via_api(supplier)
        if risk_data:
            score = risk_data.get("risk_score", 0)
            level = risk_data.get("risk_level", "UNKNOWN")
            result["risk_check"] = {
                "score": score,
                "level": level,
                "summary": risk_data.get("risk_summary", "")[:200]
            }
            log(f"  ✅ Risk Score: {score}/100 ({level})")

            # Alert if high/critical
            if score > 75:
                critical_count += 1
                alert = f"🚨 CRITICAL: {name} — Risk Score {score}/100"
                alerts.append(alert)
                result["alerts"].append(alert)
                log(f"  {alert}")
            elif score > 50:
                high_risk_count += 1
                alert = f"⚠️  HIGH RISK: {name} — Risk Score {score}/100"
                alerts.append(alert)
                result["alerts"].append(alert)
                log(f"  {alert}")
        else:
            log(f"  ❌ Risk check failed")

        # Cyber risk check
        log(f"  🔐 Cyber risk check...")
        cyber_data = await cyber_check_via_api(supplier)
        if cyber_data:
            cyber_score = cyber_data.get("cyber_risk_score", 0)
            cyber_level = cyber_data.get("risk_level", "UNKNOWN")
            result["cyber_check"] = {
                "score": cyber_score,
                "level": cyber_level,
                "key_findings": cyber_data.get("ai_analysis", {}).get("key_vulnerabilities", [])[:3]
            }
            log(f"  ✅ Cyber Risk: {cyber_score}/100 ({cyber_level})")

            if cyber_score > 70:
                alert = f"🔐 CYBER ALERT: {name} — Cyber Risk {cyber_score}/100"
                alerts.append(alert)
                result["alerts"].append(alert)
                log(f"  {alert}")
        else:
            log(f"  ⚠️  Cyber check skipped (API not ready)")

        # Small delay between suppliers
        await asyncio.sleep(2)
        audit_results.append(result)

    # Summary
    end_time = datetime.now(timezone.utc)
    duration = (end_time - start_time).total_seconds()

    summary = {
        "run_timestamp": start_time.isoformat(),
        "completed_at": end_time.isoformat(),
        "duration_seconds": round(duration, 1),
        "total_suppliers_checked": len(suppliers),
        "critical_count": critical_count,
        "high_risk_count": high_risk_count,
        "total_alerts": len(alerts),
        "alerts": alerts,
        "results": audit_results,
        "status": "completed"
    }

    # Save
    history = load_audit_history()
    history.append({
        "timestamp": start_time.isoformat(),
        "summary": {k: v for k, v in summary.items() if k != "results"},
    })
    save_audit_history(history)
    save_summary(summary)

    log("\n" + "=" * 60)
    log(f"✅ Audit Complete!")
    log(f"   Suppliers checked: {len(suppliers)}")
    log(f"   Critical alerts:   {critical_count}")
    log(f"   High risk alerts:  {high_risk_count}")
    log(f"   Duration:          {duration:.1f}s")
    log("=" * 60)

    return summary


if __name__ == "__main__":
    asyncio.run(run_nightly_audit())
