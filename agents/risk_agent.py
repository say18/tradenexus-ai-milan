from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url="https://api.featherless.ai/v1",
    api_key=os.getenv("FEATHERLESS_API_KEY")
)

def calculate_risk_score(supplier_name: str, news_summary: str, industry: str = "") -> dict:
    prompt = f"""
You are a supply chain risk analyst. Analyze this supplier and give a risk score.

SUPPLIER: {supplier_name}
INDUSTRY: {industry if industry else "general"}
NEWS SUMMARY:
{news_summary}

Provide your response in EXACTLY this format:
SCORE: [0-100]
LEVEL: [LOW / MODERATE / HIGH / CRITICAL]
FACTORS:
- [factor 1]
- [factor 2]
- [factor 3]
ACTIONS:
- [action 1]
- [action 2]
- [action 3]
CONFIDENCE: [LOW / MEDIUM / HIGH]
SUMMARY: [2 sentence summary]

Score guide:
0-25 = LOW RISK
26-50 = MODERATE RISK  
51-75 = HIGH RISK
76-100 = CRITICAL RISK
"""

    try:
        response = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-R1-0528",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert supply chain risk analyst. Always respond in the exact format requested."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=800,
            temperature=0.1
        )

        raw = response.choices[0].message.content
        parsed = parse_risk_response(raw)
        parsed["supplier"] = supplier_name
        return parsed

    except Exception as e:
        return {
            "supplier": supplier_name,
            "score": 50,
            "level": "MODERATE",
            "factors": [f"Analysis error: {str(e)}"],
            "actions": ["Manual review required"],
            "confidence": "LOW",
            "summary": "Risk assessment could not be completed."
        }


def parse_risk_response(text: str) -> dict:
    result = {
        "score": 50,
        "level": "MODERATE",
        "factors": [],
        "actions": [],
        "confidence": "MEDIUM",
        "summary": ""
    }

    lines = text.strip().split('\n')
    current_section = None

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("SCORE:"):
            try:
                result["score"] = int(''.join(filter(str.isdigit, line.split(":")[1])))
            except:
                pass
        elif line.startswith("LEVEL:"):
            result["level"] = line.split(":")[1].strip()
        elif line.startswith("FACTORS:"):
            current_section = "factors"
        elif line.startswith("ACTIONS:"):
            current_section = "actions"
        elif line.startswith("CONFIDENCE:"):
            result["confidence"] = line.split(":")[1].strip()
            current_section = None
        elif line.startswith("SUMMARY:"):
            result["summary"] = line.replace("SUMMARY:", "").strip()
            current_section = None
        elif line.startswith("- ") and current_section in ["factors", "actions"]:
            result[current_section].append(line[2:])

    return result


if __name__ == "__main__":
    test_news = "CEO resigned, missed debt payment $500M, factory flooded."
    result = calculate_risk_score("Test Supplier", test_news, "manufacturing")
    print(f"Score: {result['score']}/100 — {result['level']}")
    print(f"Summary: {result['summary']}")