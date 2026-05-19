from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url="https://api.featherless.ai/v1",
    api_key=os.getenv("FEATHERLESS_API_KEY")
)

def generate_outreach_email(
    buyer_company: str,
    buyer_country: str,
    buyer_type: str,
    seller_company: str,
    product: str,
    industry: str
) -> dict:
    """
    Personalized cold email draft করে প্রতিটা buyer-এর জন্য
    """
    prompt = f"""
You are an expert B2B sales copywriter.

Write a professional cold outreach email:

SENDER (Our Company): {seller_company}
PRODUCT/SERVICE: {product}
INDUSTRY: {industry}

RECIPIENT:
- Company: {buyer_company}
- Country: {buyer_country}
- Type: {buyer_type}

Write a compelling cold email that:
1. Has a strong subject line
2. Opens with something specific about their business
3. Explains what we offer clearly
4. Shows the value proposition
5. Has a clear call to action
6. Is professional but not too formal
7. Is under 200 words

Format EXACTLY like this:
SUBJECT: [email subject line]

EMAIL:
[email body here]

FOLLOW_UP: [one line follow-up message to send after 3 days]
"""

    try:
        response = client.chat.completions.create(
            model="Qwen/Qwen2.5-72B-Instruct",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert B2B sales copywriter who writes compelling, personalized cold emails that get responses."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=600,
            temperature=0.6
        )

        raw = response.choices[0].message.content
        parsed = parse_email(raw)

        return {
            "status": "success",
            "buyer_company": buyer_company,
            "subject": parsed["subject"],
            "email_body": parsed["email_body"],
            "follow_up": parsed["follow_up"],
            "raw_response": raw,
            "source": "Featherless AI — Qwen 2.5 72B"
        }

    except Exception as e:
        return {
            "status": "error",
            "buyer_company": buyer_company,
            "subject": "Error generating email",
            "email_body": f"Error: {str(e)}",
            "follow_up": "",
            "source": "error"
        }


def parse_email(text: str) -> dict:
    result = {
        "subject": "",
        "email_body": "",
        "follow_up": ""
    }

    lines = text.strip().split('\n')
    current_section = None
    body_lines = []

    for line in lines:
        if line.startswith('SUBJECT:'):
            result["subject"] = line.replace('SUBJECT:', '').strip()
        elif line.startswith('EMAIL:'):
            current_section = "email"
        elif line.startswith('FOLLOW_UP:'):
            current_section = "follow_up"
            result["follow_up"] = line.replace('FOLLOW_UP:', '').strip()
        elif current_section == "email" and not line.startswith('FOLLOW_UP:'):
            body_lines.append(line)

    result["email_body"] = '\n'.join(body_lines).strip()
    return result


if __name__ == "__main__":
    result = generate_outreach_email(
        buyer_company="Fashion House Berlin",
        buyer_country="Germany",
        buyer_type="retailer",
        seller_company="Dhaka Leather Co.",
        product="handmade leather bags",
        industry="fashion"
    )
    print(f"Subject: {result['subject']}")
    print(f"\nEmail:\n{result['email_body']}")