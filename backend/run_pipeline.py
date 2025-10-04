# backend/run_pipeline.py
from pathlib import Path
import shutil
import backend.code1 as code1
import backend.code2 as code2
import backend.code5 as code5
import backend.code6 as code6
import backend.code7 as code7

def run_automated_pipeline(file_path, output_folder):
    """
    Run code1 → code2.
    Input: PDF file
    Output: code2_output.json in output_folder
    """
    output_folder = Path(output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)

    print(f"\n🔹 Running code1 (PDF → text) for {Path(file_path).name}")
    code1.process(file_path, output_folder)

    print(f"🔹 Running code2 (text → extracted JSON) for {Path(file_path).name}")
    code2.process(output_folder)

    return output_folder / "code2_output.json"


def run_manual_steps(output_folder):
    """
    Run code5 → code6 and generate final_output_form_keys_filled.json
    """
    output_folder = Path(output_folder)

    print(f"\n🔹 Running code5 (map mandatory fields) in {output_folder}")
    code5.process(output_folder)

    print(f"🔹 Running code6 (ask user for empty mandatory/optional fields)")
    code6.process(output_folder)

    code6_output = output_folder / "code6_output_form_keys_filled.json"
    final_output = output_folder / "final_output_form_keys_filled.json"

    if code6_output.exists():
        shutil.copy(code6_output, final_output)
        print(f"✅ Final output generated: {final_output.name}")
    else:
        raise FileNotFoundError(f"{code6_output} not found after code6 processing")

    return final_output


def run_full_pipeline(file_path, output_folder, session_json_file, override: bool = False):
    """
    Run full pipeline for a single PDF, integrating session logic.
    - First PDF: run manual steps (code5 → code6)
    - Subsequent PDFs: copy code2_output.json → final_output_form_keys_filled.json
      and merge into session JSON
    """
    output_folder = Path(output_folder)
    session_json_file = Path(session_json_file)

    print(f"\n{'='*70}\n🎯 Processing PDF: {Path(file_path).name}\n{'='*70}\n")

    # Step 1-2: Automated (code1 → code2)
    run_automated_pipeline(file_path, output_folder)

    first_pdf = not session_json_file.exists()

    if first_pdf:
        print("🆕 First PDF → Running manual steps (code5 → code6)")
        run_manual_steps(output_folder)
    else:
        # Subsequent PDFs: generate final_output_form_keys_filled.json from code2 output
        # by simply mapping extracted values to form_keys
        src = output_folder / "code2_output.json"
        dest = output_folder / "final_output_form_keys_filled.json"
        shutil.copy(src, dest)
        print(f"📄 Copied code2 output → {dest.name} for subsequent PDF (no manual steps)")

    # Merge into session-level JSON
    code7.merge_pdf_into_session(str(output_folder), str(session_json_file), override)

    print(f"\n{'='*70}\n✅ Pipeline Completed for {Path(file_path).name}")
    print(f"Session JSON updated at: {session_json_file}\n{'='*70}\n")

    return session_json_file


# CLI support
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 4:
        print("Usage: python run_pipeline.py <input_file> <pdf_output_folder> <session_json_file> [override]")
        sys.exit(1)

    input_file = sys.argv[1]
    pdf_folder = sys.argv[2]
    session_json = sys.argv[3]
    override_flag = None
    if len(sys.argv) > 4:
        override_flag = sys.argv[4].lower() in ["true", "1", "yes"]

    run_full_pipeline(input_file, pdf_folder, session_json, override_flag)
