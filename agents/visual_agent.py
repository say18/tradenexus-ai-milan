from openai import OpenAI
import os
import base64
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url="https://api.featherless.ai/v1",
    api_key=os.getenv("FEATHERLESS_API_KEY")
)

# Featherless-এ available vision models — fallback order
VISION_MODELS = [
    "Qwen/Qwen2-VL-7B-Instruct",
    "Qwen/Qwen2-VL-72B-Instruct",
    "mistralai/Pixtral-12B-2409",
    "mistralai/Mistral-Small-3.1-24B-Instruct-2503",
    "meta-llama/Llama-3.2-11B-Vision-Instruct",
    "meta-llama/Llama-3.2-90B-Vision-Instruct",
]


def call_vision_model(image_data: str, mime_type: str, prompt: str) -> str:
    """Vision models একে একে try করে — যেটা কাজ করে সেটা use করে।"""
    last_error = ""

    for model in VISION_MODELS:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{image_data}"
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ],
                max_tokens=800,
                temperature=0.2
            )
            return response.choices[0].message.content, model
        except Exception as e:
            last_error = str(e)
            # Model not available — try next
            if "not_deployed" in last_error or "not available" in last_error or "400" in last_error:
                continue
            else:
                # Other error (auth, network) — stop trying
                break

    return None, last_error


def analyze_factory_image(image_path: str, supplier_name: str = "") -> dict:
    """
    Factory/warehouse photo analyze করে physical risk detect করে।
    Featherless vision models use করে — automatic fallback।
    """
    try:
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")

        ext = image_path.lower().split('.')[-1]
        mime_types = {
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'webp': 'image/webp',
            'gif': 'image/gif',
        }
        mime_type = mime_types.get(ext, 'image/jpeg')

        prompt = f"""You are a factory safety and risk assessment expert.

Analyze this factory/warehouse/facility image for supplier: "{supplier_name}"

Look for and report on:
1. PHYSICAL CONDITION: Building structure, equipment condition
2. SAFETY ISSUES: Any visible hazards, unsafe conditions
3. CAPACITY: How busy/operational does it look?
4. RED FLAGS: Flood damage, fire damage, structural issues, abandoned equipment
5. POSITIVE SIGNS: Modern equipment, organized workspace, good condition

Format EXACTLY like this:
CONDITION: [POOR/FAIR/GOOD/EXCELLENT]
SAFETY_LEVEL: [HIGH_RISK/MODERATE_RISK/LOW_RISK/SAFE]
RED_FLAGS:
- [flag 1 or "None detected"]
POSITIVE_SIGNS:
- [sign 1 or "None detected"]
CAPACITY_STATUS: [IDLE/LOW/MODERATE/FULL]
VISUAL_RISK_SCORE: [0-100]
SUMMARY: [2-3 sentence description and overall assessment]"""

        raw, model_used = call_vision_model(image_data, mime_type, prompt)

        if raw is None:
            # Vision model unavailable — use text-only fallback
            return _text_only_fallback(supplier_name, model_used)

        parsed = parse_visual_response(raw)

        return {
            "status": "success",
            "supplier": supplier_name,
            "raw_analysis": raw,
            "parsed": parsed,
            "source": f"Featherless AI — {model_used}"
        }

    except Exception as e:
        return {
            "status": "error",
            "supplier": supplier_name,
            "raw_analysis": f"Visual analysis failed: {str(e)}",
            "parsed": {},
            "source": "error"
        }


def _text_only_fallback(supplier_name: str, error: str) -> dict:
    """Vision model না থাকলে text-only analysis দেয়।"""
    try:
        response = client.chat.completions.create(
            model="Qwen/Qwen2.5-72B-Instruct",
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"A factory/warehouse image was uploaded for supplier '{supplier_name}' "
                        f"but vision analysis is currently unavailable. "
                        f"Please provide a template risk assessment response in the exact format below, "
                        f"noting that manual visual inspection is required.\n\n"
                        f"CONDITION: UNKNOWN\n"
                        f"SAFETY_LEVEL: MODERATE_RISK\n"
                        f"RED_FLAGS:\n- Visual analysis unavailable — manual inspection required\n"
                        f"POSITIVE_SIGNS:\n- Image successfully uploaded\n"
                        f"CAPACITY_STATUS: UNKNOWN\n"
                        f"VISUAL_RISK_SCORE: 50\n"
                        f"SUMMARY: Vision analysis could not be performed automatically. "
                        f"Please manually inspect the uploaded image for {supplier_name}. "
                        f"A physical site visit is recommended for accurate risk assessment."
                    )
                }
            ],
            max_tokens=300,
            temperature=0.1
        )
        raw = response.choices[0].message.content
    except Exception:
        raw = (
            "CONDITION: UNKNOWN\n"
            "SAFETY_LEVEL: MODERATE_RISK\n"
            "RED_FLAGS:\n- Vision model unavailable — manual inspection required\n"
            "POSITIVE_SIGNS:\n- Image uploaded successfully\n"
            "CAPACITY_STATUS: UNKNOWN\n"
            "VISUAL_RISK_SCORE: 50\n"
            f"SUMMARY: Automatic visual analysis is currently unavailable. "
            f"Please manually review the uploaded image for {supplier_name}."
        )

    parsed = parse_visual_response(raw)

    return {
        "status": "partial",
        "supplier": supplier_name,
        "raw_analysis": raw,
        "parsed": parsed,
        "source": "Text fallback — vision model unavailable",
        "note": f"Vision error: {error[:100]}"
    }


def parse_visual_response(text: str) -> dict:
    result = {
        "condition": "UNKNOWN",
        "safety_level": "MODERATE_RISK",
        "red_flags": [],
        "positive_signs": [],
        "capacity_status": "UNKNOWN",
        "visual_risk_score": 50,
        "summary": ""
    }

    lines = text.strip().split('\n')
    current_section = None

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith('CONDITION:'):
            result["condition"] = line.replace('CONDITION:', '').strip()
        elif line.startswith('SAFETY_LEVEL:'):
            result["safety_level"] = line.replace('SAFETY_LEVEL:', '').strip()
        elif line.startswith('RED_FLAGS:'):
            current_section = "red_flags"
        elif line.startswith('POSITIVE_SIGNS:'):
            current_section = "positive_signs"
        elif line.startswith('CAPACITY_STATUS:'):
            result["capacity_status"] = line.replace('CAPACITY_STATUS:', '').strip()
            current_section = None
        elif line.startswith('VISUAL_RISK_SCORE:'):
            try:
                result["visual_risk_score"] = int(
                    ''.join(filter(str.isdigit, line.split(':')[1][:4]))
                )
            except:
                pass
            current_section = None
        elif line.startswith('SUMMARY:'):
            result["summary"] = line.replace('SUMMARY:', '').strip()
            current_section = None
        elif line.startswith('- ') and current_section in ["red_flags", "positive_signs"]:
            result[current_section].append(line[2:])

    return result


if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "test.jpg"
    name = sys.argv[2] if len(sys.argv) > 2 else "Test Factory"
    result = analyze_factory_image(path, name)
    print(result["raw_analysis"])
    print(f"\nSource: {result['source']}")