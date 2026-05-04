"""Generate an answer from retrieved documents using Groq."""

from __future__ import annotations

from typing import Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

from src.utils.config import Config


def _build_context(retrieved_docs: list[dict[str, Any]]) -> str:
	"""Format retrieved documents into a single context string."""
	if not retrieved_docs:
		return ""

	sections: list[str] = []
	for index, doc in enumerate(retrieved_docs, start=1):
		source = doc.get("metadata", {}).get("source", "unknown")
		content = str(doc.get("content", "")).strip()
		sections.append(f"Document {index} (source: {source}):\n{content}")
	return "\n\n".join(sections)


def generate_answer(question: str, retrieved_docs: list[dict[str, Any]]) -> str:
	"""Generate a context-only answer and return 'I don't know' when needed."""
	if not retrieved_docs:
		return "I don't know"

	context = _build_context(retrieved_docs)
	if not context.strip():
		return "I don't know"

	prompt = ChatPromptTemplate.from_messages(
		[
			(
				"system",
				"You answer only from the provided context. "
				"If the context does not contain the answer, reply exactly: I don't know.",
			),
			("human", "Question: {question}\n\nContext:\n{context}"),
		]
	)

	model_name = Config.get_env_variable("GROQ_MODEL", "llama-3.1-8b-instant")

	llm = ChatGroq(
		model=model_name,
		temperature=0,
		groq_api_key=Config.get_groq_api_key(),
	)

	messages = prompt.format_messages(question=question, context=context)
	response = llm.invoke(messages)
	answer = str(response.content).strip()

	return answer or "I don't know"
