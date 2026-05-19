from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url="https://api.featherless.ai/v1",
    api_key=os.getenv("FEATHERLESS_API_KEY")
)

def find_global_buyers(product: str, industry: str, target_region: str = "Europe") -> dict:
    """
    Global buyers/importers খোঁজে
    Featherless Qwen দিয়ে
    """
    prompt = f"""
You are a global trade and business development expert.

Find potential buyers/importers for:
PRODUCT: {product}
INDUSTRY: {industry}
TARGET REGION: {target_region}

Provide 5 potential buyer companies in this EXACT format:

BUYER 1:
- Company: [company name]
- Country: [country]
- Type: [importer/retailer/distributor/manufacturer]
- Size: [small/medium/large]
- Why Good Fit: [one line reason]
- Estimated Contact: [generic email format like info@company.com]

BUYER 2:
- Company: [company name]
- Country: [country]
- Type: [importer/retailer/distributor/manufacturer]
- Size: [small/medium/large]
- Why Good Fit: [one line reason]
- Estimated Contact: [generic email format]

BUYER 3:
- Company: [company name]
- Country: [country]
- Type: [importer/retailer/distributor/manufacturer]
- Size: [small/medium/large]
- Why Good Fit: [one line reason]
- Estimated Contact: [generic email format]

BUYER 4:
- Company: [company name]
- Country: [country]
- Type: [importer/retailer/distributor/manufacturer]
- Size: [small/medium/large]
- Why Good Fit: [one line reason]
- Estimated Contact: [generic email format]

BUYER 5:
- Company: [company name]
- Country: [country]
- Type: [importer/retailer/distributor/manufacturer]
- Size: [small/medium/large]
- Why Good Fit: [one line reason]
- Estimated Contact: [generic email format]

MARKET INSIGHT: [2 sentence overview of this market opportunity]
BEST REGION: [which specific country/region has most opportunity]
"""

    try:
        response = client.chat.completions.create(
            model="Qwen/Qwen2.5-72B-Instruct",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert in global trade, import/export, and business development. Provide realistic and helpful buyer recommendations."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=1200,
            temperature=0.4
        )

        raw = response.choices[0].message.content
        buyers = parse_buyers(raw)

        return {
            "status": "success",
            "product": product,
            "target_region": target_region,
            "raw_response": raw,
            "buyers": buyers,
            "source": "Featherless AI — Qwen 2.5 72B"
        }

    except Exception as e:
        return {
            "status": "error",
            "product": product,
            "raw_response": f"Error: {str(e)}",
            "buyers": [],
            "source": "error"
        }


def parse_buyers(text: str) -> list:
    """Raw text থেকে buyer list বের করো"""
    buyers = []
    current_buyer = {}

    for line in text.split('\n'):
        line = line.strip()
        if line.startswith('BUYER'):
            if current_buyer:
                buyers.append(current_buyer)
            current_buyer = {}
        elif line.startswith('- Company:'):
            current_buyer['company'] = line.replace('- Company:', '').strip()
        elif line.startswith('- Country:'):
            current_buyer['country'] = line.replace('- Country:', '').strip()
        elif line.startswith('- Type:'):
            current_buyer['type'] = line.replace('- Type:', '').strip()
        elif line.startswith('- Size:'):
            current_buyer['size'] = line.replace('- Size:', '').strip()
        elif line.startswith('- Why Good Fit:'):
            current_buyer['fit_reason'] = line.replace('- Why Good Fit:', '').strip()
        elif line.startswith('- Estimated Contact:'):
            current_buyer['contact'] = line.replace('- Estimated Contact:', '').strip()

    if current_buyer:
        buyers.append(current_buyer)

    return buyers


if __name__ == "__main__":
    result = find_global_buyers("handmade leather bags", "fashion", "Europe")
    print(result["raw_response"])