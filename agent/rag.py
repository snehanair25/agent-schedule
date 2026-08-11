"""
Builds a Chroma vector store from the simulated event history, and provides
a retrieval function that finds similar past events for a new incoming event.
Embeddings run locally via sentence-transformers, so no API calls needed here.
"""

import json
from pathlib import Path

from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
PERSIST_DIR = "vectorstore/chroma_db"

def _load_embeddings():
    return HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

def build_vectorstore(history_path="data/event_history.json", persist_dir=PERSIST_DIR):
    """Embeds every past event's reasoning text and stores it in Chroma."""
    with open(history_path) as f:
        events = json.load(f)

    docs = []
    for i, e in enumerate(events):
        docs.append(Document(
            page_content=e["reasoning"],
            metadata={
                "day": e["day"],
                "category": e["category"],
                "fatigue_score": e["fatigue_score"],
                "decision": e["decision"],
                "duration_hours": e["duration_hours"],
                "date": e["date"],
            },
            id=str(i),
        ))

    embeddings = _load_embeddings()
    Path(persist_dir).mkdir(parents=True, exist_ok=True)

    vectorstore = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        persist_directory=persist_dir,
    )
    print(f"Embedded {len(docs)} events into vector store at {persist_dir}")
    return vectorstore

def load_vectorstore(persist_dir=PERSIST_DIR):
    """Loads the vector store, building it first if it doesn't exist yet."""
    if not Path(persist_dir).exists():
        build_vectorstore(persist_dir=persist_dir)
    embeddings = _load_embeddings()
    return Chroma(persist_directory=persist_dir, embedding_function=embeddings)

def retrieve_similar_events(query_text, k=3, persist_dir=PERSIST_DIR):
    """
    Given a description of a new incoming event, retrieves the k most similar
    past events (with their decisions) from the vector store.
    """
    vectorstore = load_vectorstore(persist_dir)
    results = vectorstore.similarity_search(query_text, k=k)
    return results

if __name__ == "__main__":
    build_vectorstore()

    # Quick sanity check: retrieve events similar to a hypothetical new one
    test_query = "A social event on a Tuesday with high fatigue"
    print(f"\nTest retrieval for: '{test_query}'\n")
    matches = retrieve_similar_events(test_query, k=3)
    for m in matches:
        print(f"- {m.page_content}  [decision: {m.metadata['decision']}]")