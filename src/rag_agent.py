"""Simple retrieval-augmented generation pipeline."""

from __future__ import annotations

from src.nodes.generate import generate_answer
from src.nodes.retrieve import retrieve_documents
from src.utils.logger import logger


def run_rag(question: str) -> str:
	"""Retrieve documents for a question and generate a final answer."""
	retrieved_docs = retrieve_documents(question, top_k=3)

	print("Retrieved documents:")
	if not retrieved_docs:
		print("- No matching documents found.")
	else:
		for index, doc in enumerate(retrieved_docs, start=1):
			source = doc.get("metadata", {}).get("source", "unknown")
			content = str(doc.get("content", "")).strip()
			print(f"{index}. source={source}")
			print(content)
			print("-")

	answer = generate_answer(question, retrieved_docs)

	print("Final answer:")
	print(answer)

	return answer


if __name__ == "__main__":
	try:
		user_question = input("Ask a question: ").strip()
		if not user_question:
			logger.error("No question provided.")
		else:
			run_rag(user_question)
	except Exception as exc:
		logger.error("RAG pipeline failed: %s", exc, exc_info=True)
