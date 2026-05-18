import os
import pdfplumber


def _detect_language(filename: str) -> str:
    name = filename.upper()
    if "(DE)" in name:
        return "german"
    if "(FR)" in name:
        return "french"
    if "(IT TRANSLATED)" in name or "(IT)" in name:
        return "italian"
    if "(ES TRANSLATED)" in name or "(ES)" in name:
        return "spanish"
    return "english"  # (UK), (LDN), or no language suffix


def load_pdfs(folder_path: str) -> list[dict]:
    chunks = []
    for filename in sorted(os.listdir(folder_path)):
        if not filename.endswith(".pdf"):
            continue
        language = _detect_language(filename)
        filepath = os.path.join(folder_path, filename)
        with pdfplumber.open(filepath) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                text = page.extract_text()
                if not text or not text.strip():
                    continue
                chunks.append({
                    "id": f"{filename}_page{page_num}",
                    "text": text.strip(),
                    "source": filename,
                    "page": page_num,
                    "language": language,
                })
    return chunks
