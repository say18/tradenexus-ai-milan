import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url="https://api.featherless.ai/v1",
    api_key=os.getenv("FEATHERLESS_API_KEY")
)


def calculate_hhi(market_shares: list) -> float:
    """Herfindahl-Hirschman Index (HHI) calculate করে।
    HHI = sum of squared market shares (%)
    < 1500 = Competitive
    1500-2500 = Moderately Concentrated
    > 2500 = Highly Concentrated (Monopoly risk)
    """
    return sum(share ** 2 for share in market_shares)


def utility_maximization(budget: float, options: list) -> dict:
    """
    Utility Maximization — limited budget-এ best deal বের করে।
    options = [{"name": "X", "price_per_unit": 10, "quality_score": 8, "units": 100}, ...]
    Utility = quality_score / price_per_unit (value per dollar)
    """
    if not options or budget <= 0:
        return {"error": "Invalid input"}

    # Calculate utility per dollar for each option
    for opt in options:
        price = opt.get("price_per_unit", 1)
        quality = opt.get("quality_score", 5)
        opt["utility_per_dollar"] = round(quality / price, 4)
        opt["total_cost"] = round(opt.get("units", 1) * price, 2)
        opt["affordable"] = opt["total_cost"] <= budget

    # Sort by utility per dollar (best value first)
    ranked = sorted(options, key=lambda x: x["utility_per_dollar"], reverse=True)

    # Find optimal allocation within budget
    remaining = budget
    selected = []
    for opt in ranked:
        if opt["total_cost"] <= remaining:
            selected.append(opt)
            remaining -= opt["total_cost"]

    return {
        "ranked_options": ranked,
        "optimal_selection": selected,
        "total_spent": round(budget - remaining, 2),
        "remaining_budget": round(remaining, 2),
        "budget_utilization_pct": round((budget - remaining) / budget * 100, 1)
    }


async def run_micro_econ_analysis(
    commodity: str,
    industry: str,
    budget: float,
    suppliers: list,
    country: str = "Bangladesh"
) -> dict:
    """
    Main Micro-Econ Agent:
    1. Supplier market power (HHI) analyze করে
    2. Utility Maximization দিয়ে best purchase decision দেয়
    3. Featherless AI দিয়ে strategic recommendation দেয়
    """

    # Step 1: HHI Calculation
    market_shares = [s.get("market_share_pct", 20) for s in suppliers]
    if not market_shares:
        market_shares = [100]

    hhi = calculate_hhi(market_shares)

    if hhi < 1500:
        market_structure = "COMPETITIVE"
        monopoly_risk = "LOW"
    elif hhi < 2500:
        market_structure = "MODERATELY_CONCENTRATED"
        monopoly_risk = "MEDIUM"
    else:
        market_structure = "HIGHLY_CONCENTRATED"
        monopoly_risk = "HIGH"

    # Step 2: Utility Maximization
    options = []
    for s in suppliers:
        options.append({
            "name": s.get("name", "Unknown"),
            "price_per_unit": s.get("price_per_unit", 10),
            "quality_score": s.get("quality_score", 5),
            "units": s.get("units_needed", 100),
            "lead_time_days": s.get("lead_time_days", 30),
            "risk_score": s.get("risk_score", 50)
        })

    utility_result = utility_maximization(budget, options)

    # Step 3: AI Strategic Analysis
    prompt = f"""You are a microeconomics expert and supply chain strategist.

Analyze the market for {commodity} in the {industry} industry for a buyer in {country}.

MARKET DATA:
- HHI Index: {hhi:.0f} ({market_structure})
- Monopoly Risk: {monopoly_risk}
- Buyer Budget: ${budget:,.2f}

SUPPLIERS:
{json.dumps(suppliers, indent=2)}

UTILITY MAXIMIZATION RESULT:
{json.dumps(utility_result, indent=2)}

Respond ONLY in this exact JSON format:
{{
  "market_power_assessment": {{
    "hhi": {hhi:.0f},
    "market_structure": "{market_structure}",
    "monopoly_risk": "{monopoly_risk}",
    "buyer_bargaining_power": "HIGH" or "MEDIUM" or "LOW",
    "interpretation": "One sentence explaining the market structure"
  }},
  "optimal_strategy": {{
    "recommended_action": "BUY_NOW" or "WAIT" or "NEGOTIATE" or "DIVERSIFY",
    "lock_in_percentage": <0-100, what % of budget to commit now>,
    "reasoning": "2 sentences explaining why",
    "negotiation_leverage": "One sentence about buyer's leverage"
  }},
  "utility_verdict": {{
    "best_supplier": "supplier name with highest utility",
    "utility_score": <calculated utility per dollar>,
    "total_savings_vs_worst": <estimated savings in USD>,
    "recommendation": "One clear purchase instruction"
  }},
  "risk_factors": ["factor1", "factor2"],
  "summary": "3-sentence microeconomic analysis and action plan"
}}"""

    try:
        response = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-R1",
            messages=[
                {"role": "system", "content": "You are a microeconomics expert. Respond only in valid JSON."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=900,
            temperature=0.2
        )
        raw = response.choices[0].message.content
        start = raw.find("{")
        end = raw.rfind("}") + 1
        ai_result = json.loads(raw[start:end])
    except Exception as e:
        ai_result = {
            "market_power_assessment": {
                "hhi": hhi,
                "market_structure": market_structure,
                "monopoly_risk": monopoly_risk,
                "buyer_bargaining_power": "MEDIUM",
                "interpretation": "Analysis error — manual review recommended."
            },
            "optimal_strategy": {
                "recommended_action": "NEGOTIATE",
                "lock_in_percentage": 50,
                "reasoning": "Insufficient data for full analysis.",
                "negotiation_leverage": "Seek multiple quotes."
            },
            "utility_verdict": {
                "best_supplier": utility_result.get("ranked_options", [{}])[0].get("name", "N/A"),
                "utility_score": utility_result.get("ranked_options", [{}])[0].get("utility_per_dollar", 0),
                "total_savings_vs_worst": 0,
                "recommendation": "Choose highest utility-per-dollar supplier."
            },
            "risk_factors": [str(e)[:100]],
            "summary": "Microeconomic analysis could not complete. Manual review recommended."
        }

    return {
        "status": "success",
        "commodity": commodity,
        "industry": industry,
        "budget": budget,
        "hhi": round(hhi, 0),
        "market_structure": market_structure,
        "monopoly_risk": monopoly_risk,
        "utility_maximization": utility_result,
        "ai_analysis": ai_result,
        "source": "TradeNexus Micro-Econ Agent — DeepSeek-R1"
    }


if __name__ == "__main__":
    import asyncio

    test_suppliers = [
        {"name": "Supplier A", "market_share_pct": 60, "price_per_unit": 8.5, "quality_score": 7, "units_needed": 1000, "lead_time_days": 14, "risk_score": 30},
        {"name": "Supplier B", "market_share_pct": 25, "price_per_unit": 9.2, "quality_score": 9, "units_needed": 1000, "lead_time_days": 21, "risk_score": 20},
        {"name": "Supplier C", "market_share_pct": 15, "price_per_unit": 7.8, "quality_score": 6, "units_needed": 1000, "lead_time_days": 30, "risk_score": 50},
    ]

    result = asyncio.run(run_micro_econ_analysis(
        commodity="cotton",
        industry="textile",
        budget=10000,
        suppliers=test_suppliers,
        country="Bangladesh"
    ))
    print(json.dumps(result, indent=2, default=str))
