# backend/code5.py
import json
from pathlib import Path

def process(output_folder, investor_type):
    """
    Extract mandatory fields from filled form and map values according to mandatory.json

    Args:
        output_folder: folder containing code2_output.json (filled form)
        investor_type: string, one of keys from mandatory.json["Type of Investors"]

    Returns:
        Path to code5_output_mandatory_form_key_mapping.json
    """
    output_folder = Path(output_folder)
    output_file = output_folder / "code5_output_mandatory_form_key_mapping.json"

    # Load mandatory.json
    mandatory_file = Path("mandatory.json")
    with open(mandatory_file, "r", encoding="utf-8") as f:
        mandatory_data = json.load(f)["Type of Investors"]

    if investor_type not in mandatory_data:
        raise ValueError(f"Investor type '{investor_type}' not found in mandatory.json")

    mandatory_fields = mandatory_data[investor_type]

    # Load filled form (from code2_output.json)
    form_filled_file = output_folder / "code2_output.json"
    if not form_filled_file.exists():
        raise FileNotFoundError(f"{form_filled_file} not found. Run code2 first.")

    with open(form_filled_file, "r", encoding="utf-8") as f:
        form_filled = json.load(f)

    # Recursive function to map mandatory keys to filled values
    def map_mandatory(mand_node, form_node):
        result = {}
        for key, val in mand_node.items():
            if isinstance(val, dict):
                # Nested object → recurse
                result[key] = map_mandatory(val, form_node)
            else:
                # val is either "" or a string pointing to form_keys key
                if isinstance(val, str) and val != "":
                    # Handle nested keys with dot notation
                    keys = val.split(".")
                    temp = form_node
                    for k in keys:
                        temp = temp.get(k, {})
                    value = temp.get("value", "")
                    result[key] = {"value": value}
                else:
                    # Keep empty
                    result[key] = {"value": ""}
        return result

    mapped_mandatory = map_mandatory(mandatory_fields, form_filled)

    # Save to file
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(mapped_mandatory, f, indent=4, ensure_ascii=False)

    print(f"✅ Mandatory fields mapped and saved to {output_file}")
    return output_file


# CLI support
if __name__ == "__main__":
    import sys
    folder = sys.argv[1]
    investor_type = sys.argv[2]
    process(folder, investor_type)
