from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url="https://api.featherless.ai/v1",
    api_key=os.getenv("FEATHERLESS_API_KEY")
)

def get_supplier_news(supplier_name: str, industry: str = "") -> dict:
    prompt = f"""
You are a supply chain intelligence analyst with knowledge up to 2025.

Analyze this supplier based on your knowledge:
SUPPLIER: {supplier_name}
INDUSTRY: {industry if industry else "general"}

Provide a detailed analysis:

1. COMPANY OVERVIEW: Brief description of the company
2. KNOWN ISSUES: Any financial problems, scandals, or risks you know about
3. RECENT DEVELOPMENTS: Latest known news or changes
4. SENTIMENT: POSITIVE / NEUTRAL / CONCERNING / CRITICAL
5. KEY RISK FACTORS: List top 3 risks
6. KEY STRENGTHS: List top 3 strengths

Be specific and factual based on your training data.
"""

    try:
        response = client.chat.completions.create(
            model="Qwen/Qwen2.5-72B-Instruct",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert supply chain analyst. Provide detailed, accurate analysis of companies and suppliers."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=1000,
            temperature=0.3
        )
        return {
            "status": "success",
            "supplier": supplier_name,
            "news_summary": response.choices[0].message.content,
            "source": "Featherless AI — Llama 3.3 70B"
        }
    except Exception as e:
        return {
            "status": "error",
            "supplier": supplier_name,
            "news_summary": f"Error: {str(e)}",
            "source": "error"
        }

if __name__ == "__main__":
    result = get_supplier_news("Evergrande", "real estate")
    print(result["news_summary"])