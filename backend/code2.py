# backend/code2.py
import os
import json
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

def process(output_folder):
    """
    Parse code1_output.txt and fill form_keys.json using GPT.

    Args:
        output_folder: Folder containing code1_output.txt
    Returns:
        Path to code2_output_filled_form_keys.json
    """
    output_folder = Path(output_folder)
    input_text_path = output_folder / "code1_output.txt"
    output_file_path = output_folder / "code2_output_filled_form_keys.json"
    
    if not input_text_path.exists():
        raise FileNotFoundError(f"{input_text_path} not found. Run code1 first.")
    
    # Load input text
    with open(input_text_path, "r", encoding="utf-8") as f:
        document_text = f.read()
    
    # Load form keys
    form_keys_path = Path(__file__).parent.parent / "form_keys.json"
    with open(form_keys_path, "r", encoding="utf-8") as f:
        form_keys = json.load(f)
    
    # Flatten fields for GPT (path + description)
    def collect_fields(form_dict, parent=""):
        fields = []
        for k, v in form_dict.items():
            path = f"{parent}.{k}" if parent else k
            if isinstance(v, dict) and "description" in v and "value" in v:
                fields.append({"path": path, "description": v["description"]})
            elif isinstance(v, dict):
                fields.extend(collect_fields(v, path))
        return fields

    field_descriptions = collect_fields(form_keys)

    # === SUPER OPTIMIZED GPT PROMPT === #
    prompt = f"""
You are given:
1. A markdown text extracted from a scanned investment subscription document.
2. A list of fields with descriptions from a standardized subscription form.

Your task:
Match values from the markdown text to each field based on the description and context. Return exact matches only. If a value is missing, return an empty string.

Return JSON like:
{{ "field.path": "value", ... }}

Example:
"Details.Name": "John Doe"
"Details.Email": "john@example.com"
...

IMPORTANT:
- Use semantic understanding to find the most relevant value
- Never invent values
- Use only what exists in the markdown

---

Markdown Text:
{document_text}

---

Field Descriptions:
"""

    for field in field_descriptions:
        prompt += f'- {field["path"]}: {field["description"]}\n'

    # === OpenAI Call ===
    load_dotenv()
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    response = client.chat.completions.create(
        model="gpt-4o",  # Change if needed
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        response_format={"type": "json_object"}
    )

    content = response.choices[0].message.content.strip()
    try:
        extracted_values = json.loads(content)
    except json.JSONDecodeError as e:
        print("❌ GPT response invalid JSON:", e)
        print("Raw:", content)
        raise

    # Apply values back to form_keys
    def apply_values(form_dict, values, parent=""):
        for k, v in form_dict.items():
            path = f"{parent}.{k}" if parent else k
            if isinstance(v, dict) and "description" in v and "value" in v:
                v["value"] = values.get(path, "")
            elif isinstance(v, dict):
                apply_values(v, values, path)

    apply_values(form_keys, extracted_values)

    with open(output_file_path, "w", encoding="utf-8") as f:
        json.dump(form_keys, f, indent=4, ensure_ascii=False)

    print(f"✅ Filled form saved to {output_file_path}")
    return output_file_path

# Subprocess compatible
if __name__ == "__main__":
    import sys
    process(sys.argv[1])
