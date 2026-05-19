import os
import json
import httpx
from dotenv import load_dotenv

load_dotenv()

FEATHERLESS_API_KEY = os.getenv("FEATHERLESS_API_KEY")
FEATHERLESS_URL = "https://api.featherless.ai/v1/chat/completions"


async def featherless_call(model_name: str, prompt: str, max_tokens: int = 1000) -> str:
    headers = {
        "Authorization": f"Bearer {FEATHERLESS_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.3,
    }
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(FEATHERLESS_URL, headers=headers, json=payload)
            data = r.json()
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Error: {str(e)}"


def parse_json(raw: str) -> dict:
    try:
        start = raw.find("{")
        end = raw.rfind("}") + 1
        return json.loads(raw[start:end])
    except Exception:
        return {}


async def tomorrow_agent(commodity: str, industry: str) -> dict:
    prompt = f"""You are a commodity market analyst with deep expertise in global trade.

Analyze the current market conditions for {commodity} in the {industry} industry and predict price movement for the next 24-48 hours.

Consider:
- Recent global supply/demand trends for {commodity}
- Geopolitical risks affecting {commodity} supply chains
- Currency fluctuations (USD, BDT, EUR)
- Seasonal patterns and recent industry news

Respond ONLY in this exact JSON format (no extra text, no markdown):
{{
  "commodity": "{commodity}",
  "timeframe": "24-48 hours",
  "direction": "UP",
  "probability": 72,
  "price_change_pct": 3.5,
  "confidence": "MEDIUM",
  "key_drivers": ["driver one", "driver two", "driver three"],
  "recommendation": "One clear action sentence for an SME owner",
  "risk_warning": "One sentence about the main risk"
}}

direction must be exactly: UP, DOWN, or STABLE
confidence must be exactly: HIGH, MEDIUM, or LOW"""

    raw = await featherless_call("deepseek-ai/DeepSeek-R1", prompt, max_tokens=600)
    result = parse_json(raw)

    if not result:
        result = {
            "commodity": commodity,
            "timeframe": "24-48 hours",
            "direction": "STABLE",
            "probability": 50,
            "price_change_pct": 0,
            "confidence": "LOW",
            "key_drivers": ["Insufficient data", "Manual verification needed"],
            "recommendation": "Monitor market closely before making decisions.",
            "risk_warning": "AI parsing error — verify manually.",
        }
    return result


async def trend_agent(industry: str, region: str = "Global") -> dict:
    prompt = f"""You are a strategic market analyst specializing in SME trade intelligence.

Analyze the {industry} industry outlook for the next 1-5 years in {region}.

Consider:
- Post-COVID supply chain restructuring
- Sustainability and ESG regulations (especially EU)
- Digital transformation trends
- Labor cost shifts in Asia
- Trade policy changes and technology disruption specific to {industry}

Respond ONLY in this exact JSON format (no extra text, no markdown):
{{
  "industry": "{industry}",
  "region": "{region}",
  "timeframe": "1-5 years",
  "growth_outlook": "MODERATE_GROWTH",
  "cagr_estimate": "6-9%",
  "confidence": "MEDIUM",
  "top_opportunities": ["opportunity one", "opportunity two", "opportunity three"],
  "top_threats": ["threat one", "threat two", "threat three"],
  "sme_action_items": ["action one", "action two", "action three"],
  "key_trends": [
    {{"trend": "Trend Name", "impact": "HIGH", "description": "One sentence description"}},
    {{"trend": "Trend Name", "impact": "MEDIUM", "description": "One sentence description"}},
    {{"trend": "Trend Name", "impact": "LOW", "description": "One sentence description"}}
  ]
}}

growth_outlook must be one of: STRONG_GROWTH, MODERATE_GROWTH, STABLE, DECLINE
impact must be: HIGH, MEDIUM, or LOW
confidence must be: HIGH, MEDIUM, or LOW"""

    raw = await featherless_call("Qwen/Qwen2.5-72B-Instruct", prompt, max_tokens=900)
    result = parse_json(raw)

    if not result:
        result = {
            "industry": industry,
            "region": region,
            "timeframe": "1-5 years",
            "growth_outlook": "MODERATE_GROWTH",
            "cagr_estimate": "N/A",
            "confidence": "LOW",
            "top_opportunities": [],
            "top_threats": [],
            "sme_action_items": [],
            "key_trends": [],
        }
    return result


async def mega_trend_agent(industry: str, country: str = "Bangladesh") -> dict:
    prompt = f"""You are a long-term strategic forecaster specializing in emerging markets.

Predict the 5-10 year mega trends that will reshape the {industry} industry for businesses in {country}.

Consider:
- Climate change and net-zero policies impact on {industry}
- AI and automation disruption timeline
- Geopolitical realignment (US-China decoupling, friend-shoring)
- {country}-specific competitive advantages and vulnerabilities
- Global regulatory changes (carbon border taxes, supply chain due diligence laws)

Respond ONLY in this exact JSON format (no extra text, no markdown):
{{
  "industry": "{industry}",
  "country": "{country}",
  "timeframe": "5-10 years",
  "overall_verdict": "GREAT_OPPORTUNITY",
  "biggest_opportunity": "One sentence describing the biggest opportunity",
  "biggest_risk": "One sentence describing the biggest risk",
  "mega_trends": [
    {{
      "name": "Trend Name",
      "probability": 80,
      "impact": "TRANSFORMATIVE",
      "description": "Two sentence description of this trend.",
      "sme_implication": "One action SMEs should take now"
    }},
    {{
      "name": "Trend Name",
      "probability": 65,
      "impact": "HIGH",
      "description": "Two sentence description.",
      "sme_implication": "One action SMEs should take now"
    }},
    {{
      "name": "Trend Name",
      "probability": 70,
      "impact": "HIGH",
      "description": "Two sentence description.",
      "sme_implication": "One action SMEs should take now"
    }}
  ],
  "survival_strategies": ["strategy one", "strategy two", "strategy three"]
}}

overall_verdict must be one of: ADAPT_OR_DIE, GREAT_OPPORTUNITY, STABLE_EVOLUTION
impact must be one of: TRANSFORMATIVE, HIGH, MEDIUM"""

    raw = await featherless_call("mistralai/Mistral-Large-Instruct-2411", prompt, max_tokens=1000)
    result = parse_json(raw)

    if not result:
        result = {
            "industry": industry,
            "country": country,
            "timeframe": "5-10 years",
            "overall_verdict": "STABLE_EVOLUTION",
            "biggest_opportunity": "N/A",
            "biggest_risk": "N/A",
            "mega_trends": [],
            "survival_strategies": [],
        }
    return result


async def run_market_pulse(commodity: str, industry: str, region: str = "Global", country: str = "Bangladesh") -> dict:
    import asyncio

    tomorrow, trend, mega = await asyncio.gather(
        tomorrow_agent(commodity, industry),
        trend_agent(industry, region),
        mega_trend_agent(industry, country),
    )

    return {
        "status": "success",
        "query": {"commodity": commodity, "industry": industry, "region": region, "country": country},
        "tomorrow": tomorrow,
        "trend": trend,
        "mega_trend": mega,
    }