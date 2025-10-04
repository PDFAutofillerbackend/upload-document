# backend/code7.py
import json
from pathlib import Path
from typing import Optional

def merge_pdf_into_session(new_pdf_folder: str, session_json_file: str, override: Optional[bool] = None):
    """
    Merge a newly processed PDF into session-level final JSON.

    Rules:
    1. Empty keys in session → auto-fill from new doc
    2. Conflicting keys → override depends on 'override' flag:
       - If override=True → always override conflicting values
       - If override=False → always preserve session values
       - If override=None → ask the user once per document
    """
    new_pdf_folder = Path(new_pdf_folder)
    session_json_file = Path(session_json_file)

    # Pick the correct JSON: final_output from code6
    new_file = new_pdf_folder / "final_output_form_keys_filled.json"
    if not new_file.exists():
        new_file = new_pdf_folder / "code6_output_form_keys_filled.json"  # fallback

    if not new_file.exists():
        raise FileNotFoundError(f"No final JSON found for {new_pdf_folder.name}")

    # Load new PDF data
    with open(new_file, "r", encoding="utf-8") as f:
        new_pdf_data = json.load(f)

    # If session JSON exists, merge into it
    if session_json_file.exists():
        with open(session_json_file, "r", encoding="utf-8") as f:
            session_data = json.load(f)

        # Detect conflicts
        conflicts_exist = False

        def detect_conflicts(target, source):
            nonlocal conflicts_exist
            for k, v in source.items():
                if k in target:
                    if isinstance(v, dict) and "value" in v:
                        if target[k].get("value") and v.get("value") and target[k]["value"] != v["value"]:
                            conflicts_exist = True
                    elif isinstance(v, dict):
                        detect_conflicts(target[k], v)

        detect_conflicts(session_data, new_pdf_data)

        # Ask user if override not provided
        if override is None and conflicts_exist:
            while True:
                choice = input(
                    "\n⚠️ Conflicting keys detected! "
                    "Do you want to override session values with new document's values? (yes/no): "
                ).strip().lower()
                if choice in ["yes", "y", "no", "n"]:
                    override_conflicts = choice in ["yes", "y"]
                    break
                print("❌ Invalid input, please type 'yes' or 'no'.")
        else:
            override_conflicts = override if override is not None else True

        # Merge logic
        def merge_dicts(target, source):
            for k, v in source.items():
                if k in target:
                    if isinstance(v, dict) and "value" in v:
                        existing_val = target[k].get("value")
                        new_val = v.get("value")
                        # Empty session → fill
                        if not existing_val and new_val:
                            target[k]["value"] = new_val
                        # Conflict → decide based on override
                        elif existing_val and new_val and existing_val != new_val:
                            if override_conflicts:
                                target[k]["value"] = new_val
                    elif isinstance(v, dict):
                        merge_dicts(target[k], v)
                else:
                    target[k] = v  # new key, add directly

        merge_dicts(session_data, new_pdf_data)

        # Save merged session JSON
        with open(session_json_file, "w", encoding="utf-8") as f:
            json.dump(session_data, f, indent=4, ensure_ascii=False)
        print(f"✅ Merged '{new_pdf_folder.name}' into session JSON: {session_json_file.name}")

    else:
        # First document → create session JSON
        session_json_file.parent.mkdir(parents=True, exist_ok=True)
        with open(session_json_file, "w", encoding="utf-8") as f:
            json.dump(new_pdf_data, f, indent=4, ensure_ascii=False)
        print(f"🆕 Created session JSON from '{new_pdf_folder.name}': {session_json_file.name}")


# CLI support for subprocess
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python code7.py <new_pdf_folder> <session_json_file> [override: yes/no]")
        sys.exit(1)

    new_pdf_folder = sys.argv[1]
    session_json_file = sys.argv[2]
    override_arg = sys.argv[3].lower() if len(sys.argv) > 3 else None
    if override_arg in ["yes", "y"]:
        override_flag = True
    elif override_arg in ["no", "n"]:
        override_flag = False
    else:
        override_flag = None

    merge_pdf_into_session(new_pdf_folder, session_json_file, override_flag)
