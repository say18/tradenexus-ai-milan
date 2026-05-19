from openai import OpenAI
import os
import base64
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url="https://api.featherless.ai/v1",
    api_key=os.getenv("FEATHERLESS_API_KEY")
)


def extract_pdf_text(file_path: str) -> str:
    """PDF থেকে text extract — multiple methods try করে।"""

    # Method 1: pypdf2 (older, more common)
    try:
        import PyPDF2
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            text = ""
            for i, page in enumerate(reader.pages):
                if i >= 30:
                    break
                text += (page.extract_text() or "") + "\n"
        if text.strip():
            return text[:12000]
    except Exception:
        pass

    # Method 2: pypdf (newer)
    try:
        from pypdf import PdfReader
        reader = PdfReader(file_path)
        text = ""
        for i, page in enumerate(reader.pages):
            if i >= 30:
                break
            text += (page.extract_text() or "") + "\n"
        if text.strip():
            return text[:12000]
    except Exception:
        pass

    # Method 3: pdftotext CLI
    try:
        import subprocess
        result = subprocess.run(
            ["pdftotext", file_path, "-"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout[:12000]
    except Exception:
        pass

    # Method 4: pdfminer
    try:
        from pdfminer.high_level import extract_text
        text = extract_text(file_path)
        if text.strip():
            return text[:12000]
    except Exception:
        pass

    # Method 5: Read raw bytes and find text patterns
    try:
        with open(file_path, "rb") as f:
            raw = f.read()
        # Extract readable ASCII text from PDF bytes
        import re
        text_parts = re.findall(rb'BT\s*(.*?)\s*ET', raw, re.DOTALL)
        extracted = []
        for part in text_parts[:200]:
            strings = re.findall(rb'\(([^)]{1,200})\)', part)
            for s in strings:
                try:
                    decoded = s.decode('latin-1').strip()
                    if len(decoded) > 3:
                        extracted.append(decoded)
                except Exception:
                    pass
        if extracted:
            return ' '.join(extracted)[:12000]
    except Exception:
        pass

    return ""


def analyze_document(file_path: str, supplier_name: str = "") -> dict:
    """
    PDF document analyze করে supplier financial risk বের করে।
    Featherless Qwen 2.5 72B use করে।
    """
    try:
        pdf_text = extract_pdf_text(file_path)

        if not pdf_text or len(pdf_text.strip()) < 100:
            # Last resort: analyze by filename/company name only
            pdf_text = f"Document for {supplier_name} — could not extract full text. Provide general analysis based on company name."

        prompt = f"""You are a senior financial risk analyst. Analyze this document for: "{supplier_name}"

DOCUMENT CONTENT:
{pdf_text}

Provide a thorough analysis in this EXACT format:

COMPANY_OVERVIEW: [Brief description — what company, what industry, where based]

FINANCIAL_HEALTH:
- Revenue: [latest revenue figure and trend]
- Net Earnings: [latest net earnings and trend]
- Gross Margin: [gross margin %]
- Cash Position: [cash and equivalents]
- Debt Level: [total debt or "No debt"]
- Operating Cash Flow: [cash from operations]

RED_FLAGS:
- [flag 1 — specific with numbers if available, or "None detected"]
- [flag 2]
- [flag 3]

POSITIVE_INDICATORS:
- [indicator 1 — specific with data]
- [indicator 2]
- [indicator 3]

KEY_RISKS:
- [risk 1 — from the document's own risk factors]
- [risk 2]
- [risk 3]

RISK_LEVEL: [LOW / MODERATE / HIGH / CRITICAL]

RISK_SCORE: [0-100, where 0=safest, 100=most risky]

KEY_FINDINGS:
- [finding 1 — most important]
- [finding 2]
- [finding 3]
- [finding 4]
- [finding 5]

DOCUMENT_SUMMARY: [3-4 sentence overall assessment]

SUPPLIER_RECOMMENDATION: [SAFE_TO_WORK_WITH / MONITOR_CLOSELY / HIGH_CAUTION / AVOID]"""

        response = client.chat.completions.create(
            model="Qwen/Qwen2.5-72B-Instruct",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert financial risk analyst. "
                        "Analyze documents thoroughly, extract specific numbers and facts, "
                        "and provide structured risk assessments."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500,
            temperature=0.1
        )

        raw = response.choices[0].message.content
        parsed = parse_doc_response(raw)

        return {
            "status": "success",
            "supplier": supplier_name,
            "analysis": raw,
            "parsed": parsed,
            "source": "Featherless AI — Qwen 2.5 72B"
        }

    except Exception as e:
        return {
            "status": "error",
            "supplier": supplier_name,
            "analysis": f"Document analysis failed: {str(e)}",
            "parsed": {},
            "source": "error"
        }


def parse_doc_response(text: str) -> dict:
    result = {
        "company_overview": "",
        "financial_health": [],
        "red_flags": [],
        "positive_indicators": [],
        "key_risks": [],
        "risk_level": "MODERATE",
        "risk_score": 50,
        "key_findings": [],
        "document_summary": "",
        "recommendation": ""
    }

    lines = text.strip().split('\n')
    current_section = None

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("COMPANY_OVERVIEW:"):
            result["company_overview"] = line.replace("COMPANY_OVERVIEW:", "").strip()
            current_section = None
        elif line.startswith("FINANCIAL_HEALTH:"):
            current_section = "financial_health"
        elif line.startswith("RED_FLAGS:"):
            current_section = "red_flags"
        elif line.startswith("POSITIVE_INDICATORS:"):
            current_section = "positive_indicators"
        elif line.startswith("KEY_RISKS:"):
            current_section = "key_risks"
        elif line.startswith("RISK_LEVEL:"):
            result["risk_level"] = line.replace("RISK_LEVEL:", "").strip()
            current_section = None
        elif line.startswith("RISK_SCORE:"):
            try:
                result["risk_score"] = int(''.join(filter(str.isdigit, line.split(":")[1][:4])))
            except:
                pass
            current_section = None
        elif line.startswith("KEY_FINDINGS:"):
            current_section = "key_findings"
        elif line.startswith("DOCUMENT_SUMMARY:"):
            result["document_summary"] = line.replace("DOCUMENT_SUMMARY:", "").strip()
            current_section = None
        elif line.startswith("SUPPLIER_RECOMMENDATION:"):
            result["recommendation"] = line.replace("SUPPLIER_RECOMMENDATION:", "").strip()
            current_section = None
        elif line.startswith("- ") and current_section in [
            "financial_health", "red_flags", "positive_indicators", "key_risks", "key_findings"
        ]:
            result[current_section].append(line[2:].strip())

    return result


if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "test.pdf"
    name = sys.argv[2] if len(sys.argv) > 2 else "Test Company"
    result = analyze_document(path, name)
    print(result["analysis"])