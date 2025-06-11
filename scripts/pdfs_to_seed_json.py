import os
import json
import fitz
import openai
import time
import tiktoken
from tqdm import tqdm
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed

 
from openai import AzureOpenAI

# === Load environment ===
load_dotenv()

# Setup environment (you likely already have this)
api_key = os.getenv("AZURE_OPENAI_KEY")
endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
api_version = os.getenv("AZURE_OPENAI_EMBED_VERSION")  # e.g. "2023-05-15"
deployment_name = os.getenv("AZURE_OPENAI_EMBED_DEPLOYMENT")  # Your Azure deployment name




# Initialize the client
client = AzureOpenAI(
    api_key=api_key,
    api_version=api_version,
    azure_endpoint=endpoint,
)


# === Config ===
PDF_DIRS = ["../data/HR", "../data/DMS_instructions"]
BASE_FILEURLS = ["https://hrhandbook.iom.int/system/files/policies/",
                 "https://iomint.sharepoint.com/sites/DMSPortal/Instructions/"]
DOCTYPES = ["HR Policy", "Administration Instruction"]

OUTPUT_FILE = "seed_data_iom_all.json"

# === settings ===
MAX_TOKENS_PER_CHUNK = 400
MAX_RETRIES = 3
THREAD_WORKERS = 5

# === Tokenizer ===
tokenizer = tiktoken.encoding_for_model("text-embedding-3-large")  # compatible with Azure

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

def get_embedding_with_retry(text, retries=3, delay=2):
    for attempt in range(retries):
        try:
            response = client.embeddings.create(
                input=[text],
                model=deployment_name  # This must match your deployment name in Azure
            )
            return response.data[0].embedding
        except Exception as e:
            if attempt < retries - 1:
                wait_time = delay * (2 ** attempt)
                print(f"⚠️ Retry {attempt + 1}/{retries} failed: {e}. Waiting {wait_time}s...")
                time.sleep(wait_time)
            else:
                print(f"❌ Final retry failed for embedding: {e}")
                return []



# === PDF Processing ===
import pdfplumber

def fallback_pdfplumber_text(file_path):
    texts = []
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                texts.append(page.extract_text() or "")
        return texts
    except Exception as e:
        print(f"❌ Fallback also failed for {file_path}: {e}")
        return []

def extract_text_by_page(file_path):
    texts = []
    try:
        with fitz.open(file_path) as doc:
            for page_num in range(len(doc)):
                try:
                    page = doc[page_num]
                    page_text = page.get_text()
                    texts.append(page_text)
                except Exception as page_error:
                    print(f"⚠️ Skipping page {page_num + 1} in {file_path}: {page_error}")
                    texts.append("")
        return texts
    except Exception as e:
        print(f"❌ fitz failed for {file_path}, trying fallback: {e}")
        return fallback_pdfplumber_text(file_path)

def build_chunk_record(chunk_text, metadata):
    embedding = get_embedding_with_retry(chunk_text)
    if embedding:
        return {
            **metadata,
            "embedding_3l": embedding
        }
    return None




def process_file(filename, folder_path, base_fileurl, doctype):
    file_path = os.path.join(folder_path, filename)
    fileurl = base_fileurl + filename
    pages = extract_text_by_page(file_path)
    chunk_tasks = []

    for page_num, page_text in enumerate(pages, start=1):
        paragraphs = page_text.split("\n")
        chunks = semantic_chunk(paragraphs)
        for chunk_idx, chunk in enumerate(chunks):
            metadata = {
                "filename": filename,
                "fileurl": fileurl,
                "page": page_text,
                "typedoc": doctype,
                "pagenumber": page_num,
                "chunk": chunk_idx
            }
            chunk_tasks.append((chunk, metadata))

    return chunk_tasks


# === Main Processing ===
def process_all_pdfs():
    all_tasks = []

    for folder_path, base_fileurl, doctype in zip(PDF_DIRS, BASE_FILEURLS, DOCTYPES):
        print(f"📁 Scanning folder: {folder_path}")
        for filename in os.listdir(folder_path):
            if filename.lower().endswith(".pdf"):
                print(f"📄 Processing file: {filename}")
                try:
                    tasks = process_file(filename, folder_path, base_fileurl, doctype)
                    all_tasks.extend(tasks)
                except Exception as e:
                    print(f"❌ Error processing {filename}: {e}")

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
    print(f"📁 Reading PDFs from {PDF_DIRS}")
    records = process_all_pdfs()

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

    print(f"✅ {len(records)} records written to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
