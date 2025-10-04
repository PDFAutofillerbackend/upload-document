# 🧠 Smart Document Parsing & Form Key Automation System

## 📘 Overview

This project automates **document parsing**, **data extraction**, and **form key population** using a combination of LLM-based and rule-based workflows.  
Each user session allows uploading multiple documents (PDF, DOCX, PPTX, JSON, JPEG, TXT, etc.), which are then processed and structured into a standardized JSON format resembling `form_keys.json`.

---

## 📂 Directory Structure

Each user session follows this organized structure:

samples/
└── {session_name}/
├── {doc_name}/
│ ├── pdf/
│ ├── code1_output.txt
│ ├── code2_output.json
│ ├── code5_output.json
│ ├── code6_output.json
│ └── final_output_form_keys_filled.json
└── final_{session_name}_form_keys_filled.json

yaml
Copy code

---

## ⚙️ Code Flow

### 🧩 Step 1: Session Creation

- A **new session** is created for each user (e.g., `session_001`).
- All documents and outputs for that user are stored under `samples/{session_name}/`.

---

### 📄 Step 2: Document Upload

User uploads one or more supported file types:
> `.pdf`, `.docx`, `.pptx`, `.jpeg`, `.json`, `.txt`

Each document is stored under:
samples/{session_name}/{doc_name}/pdf/

yaml
Copy code

---

### 🧠 Step 3: `code1` — Convert Document to Text

**Purpose:** Converts uploaded document into markdown-formatted text.

**Input:** Uploaded document  
**Output:**  
samples/{session_name}/{doc_name}/code1_output.txt

markdown
Copy code

---

### 🔍 Step 4: `code2` — LLM-Based Parsing

**Purpose:**  
Uses `form_keys.json` as a structural reference and parses `code1_output.txt`  
to create a JSON file that aligns closely with the form key structure.

**Input:**  

- `form_keys.json`  
- `code1_output.txt`

**Output:**  
samples/{session_name}/{doc_name}/code2_output.json

pgsql
Copy code

---

### 🧾 Step 5: `code5` — Mandatory Key Mapping (No LLM)

**Purpose:**  
Maps **mandatory keys** (like “Subscriber Type” or “Share Class”) from `form_keys.json`  
with values extracted in `code2_output.json`.  

If mandatory fields are missing, they are identified for user input.

**Output:**  
samples/{session_name}/{doc_name}/code5_output.json

pgsql
Copy code

---

### 💬 Step 6: `code6` — Chatbot-Driven Completion

**Purpose:**  
Interactive chatbot asks user to fill missing **mandatory keys**,  
then proceeds to optional keys.

**Outputs:**  

- `code6_output.json` — same structure as `code2_output.json` but with user-filled values.  
- `final_output_form_keys_filled.json` — fully populated JSON for that document.

**Location:**  
samples/{session_name}/{doc_name}/final_output_form_keys_filled.json

yaml
Copy code

---

### 🧩 Step 7: Final Session File

All individual document outputs are consolidated into a **session-level** file:
samples/{session_name}/final_{session_name}_form_keys_filled.json

yaml
Copy code

This file acts as the **master form** for the session.

---

## 🔁 Step 8: Processing Multiple Documents in Same Session

When a **new document (doc2)** is uploaded:

1. `code1` and `code2` are executed automatically.  
2. `code5` and `code6` are **skipped** (since mandatory fields were already filled earlier).  
3. Compare new JSON (`doc2/final_output_form_keys_filled.json`)  
   with session master file (`final_{session_name}_form_keys_filled.json`).

### 🧮 Comparison Logic

- If a field is **empty** in the session file but **filled** in doc2 → copy it.
- If a field has conflicting values:
  - Ask user:

    """
    Do you want to override this value? (y/n)
    """

  - If **yes**, override with new value.  
  - If **no**, retain old value.

---

## ✅ Summary of Code Responsibilities

| Code File | Function | Input | Output |
|------------|-----------|--------|---------|
| **code1** | Convert document to markdown text | Uploaded document | `code1_output.txt` |
| **code2** | Parse text into structured form keys (LLM-based) | `form_keys.json`, `code1_output.txt` | `code2_output.json` |
| **code5** | Map and validate mandatory keys (rule-based) | `form_keys.json`, `code2_output.json` | `code5_output.json` |
| **code6** | Collect missing keys via chatbot & finalize form | `code2_output.json`, user input | `code6_output.json`, `final_output_form_keys_filled.json` |

---

## 🧠 Intelligent Merge Rules

- Empty fields → auto-fill from newer doc.  
- Conflicting fields → ask for user decision.  
- Once confirmed, the **session master JSON** updates automatically.

---

## 💾 Example Final Outputs

- For individual document:  
  `samples/session_1/doc1/final_output_form_keys_filled.json`
- For entire session:  
  `samples/session_1/final_session_1_form_keys_filled.json`

---

## 🚀 Future Enhancements

- Add full versioning of session files.  
- Introduce delta comparison visualization.  
- Integrate form validation for industry-specific compliance.  
- Optionally connect to a database for session tracking.

---

## 📊 (Optional) Flow Diagram (Mermaid)

```mermaid
flowchart TD
    A[Session Created] --> B[Upload Document]
    B --> C[code1: Convert to Text]
    C --> D[code2: Parse Using form_keys.json]
    D --> E[code5: Map Mandatory Fields]
    E --> F[code6: Ask User for Missing Fields]
    F --> G[Generate final_output_form_keys_filled.json]
    G --> H[Merge into Session Master JSON]
    H --> I{New Document?}
    I -->|Yes| B
    I -->|No| J[End Session]
