from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url="https://api.featherless.ai/v1",
    api_key=os.getenv("FEATHERLESS_API_KEY")
)

def generate_daily_briefing(
    suppliers: list,
    leads: list,
    price_data: str
) -> dict:
    """
    সব data একত্রিত করে daily briefing তৈরি করে
    """

    supplier_summary = "\n".join([
        f"- {s.get('name', 'Unknown')}: Risk Score {s.get('score', 'N/A')}/100 ({s.get('level', 'N/A')})"
        for s in suppliers
    ]) if suppliers else "No suppliers analyzed yet"

    leads_summary = "\n".join([
        f"- {l.get('company', 'Unknown')} ({l.get('country', 'N/A')}): {l.get('fit_reason', 'N/A')}"
        for l in leads[:5]
    ]) if leads else "No leads found yet"

    prompt = f"""
You are a business intelligence analyst. Create a concise daily briefing.

SUPPLIER DATA:
{supplier_summary}

LEADS DATA:
{leads_summary}

MARKET/PRICE DATA:
{price_data if price_data else "No price data available"}

Create a daily briefing in this EXACT format:

BRIEFING_DATE: [today's date]

TOP_PRIORITIES:
1. [most urgent action needed]
2. [second priority]
3. [third priority]

SUPPLIER_ALERT: [one line about highest risk supplier, or "All suppliers stable"]

OPPORTUNITY: [one line about best lead opportunity]

MARKET_WATCH: [one line about most important price trend]

EXECUTIVE_SUMMARY: [3 sentences max — overall business intelligence summary for today]

RECOMMENDED_ACTION: [single most important thing to do today]
"""

    try:
        response = client.chat.completions.create(
            model="Qwen/Qwen2.5-72B-Instruct",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert business intelligence analyst who creates concise, actionable daily briefings for SME owners."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=600,
            temperature=0.3
        )

        raw = response.choices[0].message.content
        parsed = parse_briefing(raw)

        return {
            "status": "success",
            "raw_briefing": raw,
            "parsed": parsed,
            "source": "Featherless AI — Qwen 2.5 72B"
        }

    except Exception as e:
        return {
            "status": "error",
            "raw_briefing": f"Error: {str(e)}",
            "parsed": {},
            "source": "error"
        }


def parse_briefing(text: str) -> dict:
    result = {
        "date": "",
        "priorities": [],
        "supplier_alert": "",
        "opportunity": "",
        "market_watch": "",
        "executive_summary": "",
        "recommended_action": ""
    }

    lines = text.strip().split('\n')
    priority_count = 0

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith('BRIEFING_DATE:'):
            result["date"] = line.replace('BRIEFING_DATE:', '').strip()
        elif line.startswith('1.') and priority_count == 0:
            result["priorities"].append(line[2:].strip())
            priority_count += 1
        elif line.startswith('2.') and priority_count == 1:
            result["priorities"].append(line[2:].strip())
            priority_count += 1
        elif line.startswith('3.') and priority_count == 2:
            result["priorities"].append(line[2:].strip())
            priority_count += 1
        elif line.startswith('SUPPLIER_ALERT:'):
            result["supplier_alert"] = line.replace('SUPPLIER_ALERT:', '').strip()
        elif line.startswith('OPPORTUNITY:'):
            result["opportunity"] = line.replace('OPPORTUNITY:', '').strip()
        elif line.startswith('MARKET_WATCH:'):
            result["market_watch"] = line.replace('MARKET_WATCH:', '').strip()
        elif line.startswith('EXECUTIVE_SUMMARY:'):
            result["executive_summary"] = line.replace('EXECUTIVE_SUMMARY:', '').strip()
        elif line.startswith('RECOMMENDED_ACTION:'):
            result["recommended_action"] = line.replace('RECOMMENDED_ACTION:', '').strip()

    return result


if __name__ == "__main__":
    test_suppliers = [
        {"name": "Evergrande", "score": 85, "level": "CRITICAL"},
        {"name": "TSMC", "score": 30, "level": "LOW"}
    ]
    test_leads = [
        {"company": "Fashion House Berlin", "country": "Germany", "fit_reason": "Large textile importer"}
    ]
    result = generate_daily_briefing(test_suppliers, test_leads, "Cotton UP 12%")
    print(result["raw_briefing"])