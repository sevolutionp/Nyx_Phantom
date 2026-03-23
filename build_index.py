# build_index.py — Chunks wiki_data.json and stores embeddings in ChromaDB
import json
import re
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

WIKI_FILE = Path(__file__).parent / "wiki_data.json"
CHROMA_DIR = Path(__file__).parent / "chroma_db"
COLLECTION_NAME = "swg_wiki"
CHUNK_SIZE = 500       # characters per chunk
CHUNK_OVERLAP = 100    # overlap between chunks
EMBED_MODEL = "all-MiniLM-L6-v2"   # fast, small, good quality — ~80MB

def chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    paragraphs = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]
    chunks = []
    current = ""
    for para in paragraphs:
        if len(current) + len(para) > size:
            if current:
                chunks.append(current.strip())
            # Start new chunk with overlap from end of previous
            current = current[-overlap:] + " " + para if current else para
        else:
            current = (current + "\n\n" + para).strip() if current else para
    if current:
        chunks.append(current.strip())
    return chunks

def main():
    print("Loading wiki data...")
    pages = json.loads(WIKI_FILE.read_text(encoding="utf-8"))
    print(f"  {len(pages)} pages loaded")

    print(f"Loading embedding model ({EMBED_MODEL})...")
    model = SentenceTransformer(EMBED_MODEL)

    print("Setting up ChromaDB...")
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    # Clear existing collection if rebuilding
    try:
        client.delete_collection(COLLECTION_NAME)
        print("  Cleared existing collection")
    except Exception:
        pass

    collection = client.create_collection(
        COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )

    doc_ids = []
    doc_texts = []
    doc_embeddings = []
    doc_metas = []

    print("Chunking and embedding pages...")
    seen_ids = {}
    for page in pages:
        chunks = chunk_text(page["text"])
        for i, chunk in enumerate(chunks):
            base_id = f"{page['title'].replace(' ', '_')}_{i}"
            # Deduplicate IDs across pages with the same title
            if base_id in seen_ids:
                seen_ids[base_id] += 1
                doc_id = f"{base_id}_{seen_ids[base_id]}"
            else:
                seen_ids[base_id] = 0
                doc_id = base_id
            doc_ids.append(doc_id)
            doc_texts.append(chunk)
            doc_metas.append({"title": page["title"], "url": page["url"], "chunk": i})

    print(f"  {len(doc_texts)} total chunks — generating embeddings...")
    embeddings = model.encode(doc_texts, show_progress_bar=True, batch_size=64).tolist()

    print("Storing in ChromaDB...")
    # Insert in batches of 500
    batch = 500
    for i in range(0, len(doc_ids), batch):
        collection.add(
            ids=doc_ids[i:i+batch],
            documents=doc_texts[i:i+batch],
            embeddings=embeddings[i:i+batch],
            metadatas=doc_metas[i:i+batch],
        )
        print(f"  Stored {min(i+batch, len(doc_ids))}/{len(doc_ids)}")

    print(f"\nIndex built! {len(doc_ids)} chunks stored in {CHROMA_DIR}")

if __name__ == "__main__":
    main()
