from pathlib import Path
from dotenv import load_dotenv

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

import chromadb

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DOCS_PATH = BASE_DIR / "docs"

chroma_client = chromadb.PersistentClient(path="./chroma_db")

collection = chroma_client.get_or_create_collection(
    name="knowledge_base",
    metadata={"hnsw:space": "cosine"}
)

def load_and_split_documents(docs_folder: str) -> list:
    all_chunks = []

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=300,
        chunk_overlap=50,
        length_function=len
    )

    docs_path = Path(docs_folder)

    for txt_file in docs_path.glob("*.txt"):
        loader = TextLoader(str(txt_file), encoding="utf-8")
        documents = loader.load()

        chunks = text_splitter.split_documents(documents)
        all_chunks.extend(chunks)

        print(f"Loaded {len(chunks)} chunks from {txt_file.name}")

    return all_chunks

# Store chunks in ChromaDB.

def ingest_to_chromadb(chunks: list):
    documents = [chunk.page_content for chunk in chunks]
    ids = [f"chunk_{i}" for i in range(len(chunks))]
    metadatas = [
        {"source": chunk.metadata.get("source", "unknown")}
        for chunk in chunks
    ]

    collection.add(
        documents=documents,
        ids=ids,
        metadatas=metadatas
    )

    print(f"Stored {len(documents)} chunks in ChromaDB")


# Main runner.

if __name__ == "__main__":
    print("Starting ingestion...")

    chunks = load_and_split_documents(str(DOCS_PATH))

    if not chunks:
        print("No documents found!")
    else:
        ingest_to_chromadb(chunks)
        print("Ingestion complete!")