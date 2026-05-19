from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url="https://api.featherless.ai/v1",
    api_key=os.getenv("FEATHERLESS_API_KEY")
)

def get_price_trends(industry: str, supplier_country: str = "") -> dict:
    prompt = f"""
You are a commodity and raw materials price analyst.

Analyze price trends for: "{industry}" industry
{f"Country focus: {supplier_country}" if supplier_country else ""}

Based on your knowledge up to 2025, provide:

MATERIAL 1: [name] | TREND: [UP/STABLE/DOWN] | CHANGE: [estimated %] | NOTE: [brief note]
MATERIAL 2: [name] | TREND: [UP/STABLE/DOWN] | CHANGE: [estimated %] | NOTE: [brief note]
MATERIAL 3: [name] | TREND: [UP/STABLE/DOWN] | CHANGE: [estimated %] | NOTE: [brief note]
RECOMMENDATION: [BUY NOW/WAIT/MONITOR] — [one line reason]
ALERT: [any supply chain warnings, or "None"]

Be specific about materials relevant to this industry.
"""

    try:
        response = client.chat.completions.create(
            model="Qwen/Qwen2.5-72B-Instruct",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert commodity price analyst. Provide accurate market analysis."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=600,
            temperature=0.2
        )
        return {
            "status": "success",
            "industry": industry,
            "price_data": response.choices[0].message.content,
            "source": "Featherless AI — Llama 3.3 70B"
        }
    except Exception as e:
        return {
            "status": "error",
            "industry": industry,
            "price_data": f"Error: {str(e)}",
            "source": "error"
        }

if __name__ == "__main__":
    result = get_price_trends("textile", "Bangladesh")
    print(result["price_data"])