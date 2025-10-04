# backend/code1.py
from markitdown import MarkItDown
from pathlib import Path

def process(input_file, output_folder):
    """
    Extract text from document and save to code1_output.txt
    Args:
        input_file: Path to input document
        output_folder: Path to store output files (document folder)
    Returns:
        Path to code1_output.txt
    """
    output_folder = Path(output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)

    md = MarkItDown(enable_plugins=False)
    result = md.convert(input_file)

    output_file = output_folder / "code1_output.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(result.text_content)

    print(f"✅ Extracted text saved to {output_file}")
    return output_file

# 🧠 REQUIRED for subprocess to work
if __name__ == "__main__":
    import sys
    input_file = sys.argv[1]
    output_folder = sys.argv[2]
    process(input_file, output_folder)
