"""Retrieve relevant documents from the existing ChromaDB collection."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import chromadb

from src.utils.config import Config


def get_collection() -> chromadb.api.models.Collection.Collection:
	"""Open the existing ChromaDB collection used by ingestion."""
	client = chromadb.PersistentClient(path=str(Config.get_chroma_db_path()))
	return client.get_or_create_collection(name="knowledge_base")


def retrieve_documents(question: str, top_k: int = 3) -> list[dict[str, Any]]:
	"""Return the top matching documents for a user question."""
	collection = get_collection()

	if collection.count() == 0:
		return []

	results = collection.query(
		query_texts=[question],
		n_results=top_k,
		include=["documents", "metadatas", "distances"],
	)

	documents = results.get("documents", [[]])[0]
	metadatas = results.get("metadatas", [[]])[0]
	distances = results.get("distances", [[]])[0]
	ids = results.get("ids", [[]])[0]

	retrieved: list[dict[str, Any]] = []
	for index, content in enumerate(documents):
		retrieved.append(
			{
				"id": ids[index] if index < len(ids) else None,
				"content": content,
				"metadata": metadatas[index] if index < len(metadatas) else {},
				"distance": distances[index] if index < len(distances) else None,
			}
		)

	return retrieved
