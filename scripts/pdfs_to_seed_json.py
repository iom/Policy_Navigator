import os
import json
import fitz
import openai
import time
import tiktoken
from tqdm import tqdm
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed

# === Load environment ===
load_dotenv()
openai.api_type = "azure"
openai.api_key = os.getenv("AZURE_OPENAI_API_KEY")
openai.api_base = os.getenv("AZURE_OPENAI_ENDPOINT")
openai.api_version = os.getenv("AZURE_OPENAI_API_VERSION")
EMBEDDING_DEPLOYMENT = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")

# === Config ===
PDF_DIR = "./data/hr"
OUTPUT_FILE = "src/backend/fastapi_app/seed_data_iom.json"
MAX_TOKENS_PER_CHUNK = 400
BASE_FILEURL = "https://yourstorage.blob.core.windows.net/docs/"
DOCTYPE = "research-paper"
MAX_RETRIES = 3
THREAD_WORKERS = 5

# === Tokenizer ===
tokenizer = tiktoken.encoding_for_model("text-embedding-ada-002")  # compatible with Azure

def count_tokens(text):
    return len(tokenizer.encode(text))

# === Paragraph chunker ===
def semantic_chunk(paragraphs, max_tokens=MAX_TOKENS_PER_CHUNK):
    chunks = []
    current_chunk = ""
    current_tokens = 0

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        para_tokens = count_tokens(para)
        if para_tokens > max_tokens:
            # Break oversized paragraph itself
            split_points = range(0, len(para), 500)
            for i in split_points:
                part = para[i:i+500]
                if part.strip():
                    chunks.append(part.strip())
            continue

        if current_tokens + para_tokens > max_tokens:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = para
            current_tokens = para_tokens
        else:
            current_chunk += "\n" + para
            current_tokens += para_tokens

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks

# === Embedding ===
def get_embedding_with_retry(text, retries=MAX_RETRIES, delay=2):
    for attempt in range(retries):
        try:
            response = openai.Embedding.create(
                input=[text],
                engine=EMBEDDING_DEPLOYMENT
            )
            return response["data"][0]["embedding"]
        except Exception as e:
            if attempt < retries - 1:
                wait_time = delay * (2 ** attempt)
                print(f"⚠️ Retry {attempt + 1}/{retries} failed: {e}. Waiting {wait_time}s...")
                time.sleep(wait_time)
            else:
                print(f"❌ Final retry failed for embedding: {e}")
                return []

# === PDF Processing ===
def extract_text_by_page(file_path):
    try:
        doc = fitz.open(file_path)
        return [page.get_text() for page in doc]
    except Exception as e:
        print(f"❌ Could not read {file_path}: {e}")
        return []

def build_chunk_record(chunk_text, metadata):
    embedding = get_embedding_with_retry(chunk_text)
    if embedding:
        return {
            **metadata,
            "embedding_3l": embedding
        }
    return None

def process_file(filename):
    file_path = os.path.join(PDF_DIR, filename)
    fileurl = BASE_FILEURL + filename
    pages = extract_text_by_page(file_path)
    chunk_tasks = []

    for page_num, page_text in enumerate(pages, start=1):
        paragraphs = page_text.split("\n")
        chunks = semantic_chunk(paragraphs)
        for chunk_idx, chunk in enumerate(chunks):
            metadata = {
                "filename": filename,
                "fileurl": fileurl,
                "page": page_text.strip()[:200],
                "type": DOCTYPE,
                "pagenumber": page_num,
                "chunk": chunk_idx
            }
            chunk_tasks.append((chunk, metadata))

    return chunk_tasks

# === Main Processing ===
def process_all_pdfs():
    all_tasks = []
    for filename in os.listdir(PDF_DIR):
        if filename.lower().endswith(".pdf"):
            tasks = process_file(filename)
            all_tasks.extend(tasks)

    results = []
    with ThreadPoolExecutor(max_workers=THREAD_WORKERS) as executor:
        futures = [executor.submit(build_chunk_record, chunk, meta) for chunk, meta in all_tasks]
        for future in tqdm(as_completed(futures), total=len(futures), desc="Embedding chunks"):
            result = future.result()
            if result:
                results.append(result)

    # Add IDs
    for idx, record in enumerate(results, start=1):
        record["id"] = idx

    return results

def main():
    print(f"📁 Reading PDFs from {PDF_DIR}")
    records = process_all_pdfs()

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

    print(f"✅ {len(records)} records written to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
