import json
import re


def extract_json(text):
    """
    Extract JSON object from a string returned by AI
    """
    try:
        # Find first JSON-like content
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group())
        else:
            # fallback: return entire text as explanation
            return {"mission_id": "Unknown", "stage": "Unknown", "explanation": text}
    except Exception:
        return {"mission_id": "Unknown", "stage": "Unknown", "explanation": text}


def clean_text(text):
    # Remove bold and italic markdown
    clean_text = re.sub(r"(\*\*|\*|_)(.*?)\1", r"\2", text)
    # Remove heading markdown
    clean_text = re.sub(r"^#+\s*", "", clean_text, flags=re.MULTILINE)
    return clean_text
