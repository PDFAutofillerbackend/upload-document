# backend/code6.py
import json
from pathlib import Path
import shutil
from collections import defaultdict

def update_form(filled_form, form_key, value):
    """Update a single key in the nested form dictionary."""
    def recurse(d):
        if isinstance(d, dict):
            for k, v in d.items():
                if k == form_key and isinstance(v, dict) and "value" in v:
                    v["value"] = value
                    return True
                if recurse(v):
                    return True
        return False
    recurse(filled_form)

def flatten_form(filled_form, parent_key=""):
    """Flatten nested form into single-level keys with value dict."""
    flat = {}
    for k, v in filled_form.items():
        new_key = f"{parent_key}.{k}" if parent_key else k
        if isinstance(v, dict) and "value" in v:
            flat[new_key] = v["value"]
        elif isinstance(v, dict):
            flat.update(flatten_form(v, new_key))
    return flat

def process(doc_folder):
    """
    1. Load code4 + code5 outputs
    2. Ask user about empty mandatory and optional fields
    3. Handle grouped boolean fields effectively
    4. Save final JSON
    """
    doc_folder = Path(doc_folder)
    form_file = doc_folder / "code2_output.json"
    map_file = doc_folder / "code5_output_mandatory_form_key_mapping.json"

    if not form_file.exists() or not map_file.exists():
        raise FileNotFoundError("Required code4 or code5 outputs missing in doc folder")

    with open(form_file, "r", encoding="utf-8") as f:
        filled_form = json.load(f)

    with open(map_file, "r", encoding="utf-8") as f:
        mandatory_map = json.load(f)

    flat_form = flatten_form(filled_form)

    # ------------------------------
    # STEP 1 — Classify fields
    # ------------------------------
    boolean_groups_to_ask = [
        "Form PF (Investor Type)",
        "Type of Subscriber",
        "Share Class Type"
    ]

    text_fields = {}
    grouped_booleans = defaultdict(dict)
    other_booleans = {}

    for key, val in flat_form.items():
        if key.endswith(".value") and not val:
            # Determine group type
            section = next((grp for grp in boolean_groups_to_ask if grp.lower() in key.lower()), None)
            if section:
                grouped_booleans[section][key] = False
            elif any(word in key.lower() for word in ["check", "type", "status", "eligibility", "class"]):
                other_booleans[key] = False
            else:
                text_fields[key] = ""

    # ------------------------------
    # STEP 2 — Fill text fields
    # ------------------------------
    print("\n📝 Please provide the following details:\n")
    mailing_checked = False  # Flag to ask the question only once

    for key in text_fields.keys():
        short_name = key.split(".")[-2] if "." in key else key
        value = ""

        if "Address (Mailing)" in key and not mailing_checked:
            same = input("📮 Is mailing address same as registered address? (y/n): ").strip().lower()
            mailing_checked = True
            if same == "y":
                for mail_key in [k for k in text_fields if "Address (Mailing)" in k]:
                    reg_key = mail_key.replace("Address (Mailing)", "Address (Registered)")
                    if reg_key in text_fields:
                        text_fields[mail_key] = text_fields[reg_key]
                continue

        # Ask input for other fields
        if not ("Address (Mailing)" in key and same == "y"):
            value = input(f"→ {short_name.replace('_', ' ').title()}: ").strip()
            text_fields[key] = value

    # ------------------------------
    # STEP 3 — Ask grouped boolean fields
    # ------------------------------
    print("\n✅ Now select category-type options:\n")
    final_booleans = {}

    for group_name, fields in grouped_booleans.items():
        print(f"\n--- {group_name} ---")
        options = list(fields.keys())

        for i, key in enumerate(options, start=1):
            opt_name = key.split(".")[-2].replace("_", " ").title()
            print(f"{i}. {opt_name}")

        while True:
            choice = input(f"Select one or multiple (comma-separated, e.g. 1,3): ").strip()
            try:
                indices = [int(i) for i in choice.split(",") if i.strip()]
                if all(1 <= idx <= len(options) for idx in indices):
                    break
                else:
                    print("❌ Invalid input, try again.")
            except ValueError:
                print("❌ Please enter numbers separated by commas.")

        for i, key in enumerate(options, start=1):
            final_booleans[key] = i in indices

    # ------------------------------
    # STEP 4 — Combine all fields
    # ------------------------------
    combined_data = {**text_fields, **final_booleans, **other_booleans}

    # ------------------------------
    # STEP 5 — Save outputs
    # ------------------------------
    code6_file = doc_folder / "code6_output_form_keys_filled.json"
    with open(code6_file, "w", encoding="utf-8") as f:
        json.dump(combined_data, f, indent=4, ensure_ascii=False)
    print(f"✅ Mandatory + optional fields saved → {code6_file.name}")

    # Save session-level JSON if first document
    session_folder = doc_folder.parent
    session_final = session_folder / f"final_{session_folder.name}_form_keys_filled.json"
    if not session_final.exists():
        shutil.copy(code6_file, session_final)
        print(f"🆕 First document → session-level form created at {session_final.name}")

# CLI support
if __name__ == "__main__":
    import sys
    doc_folder_arg = sys.argv[1]  # Only folder path is needed
    process(doc_folder_arg)
