"""Rewrite or clarify a user question to improve retrieval results."""

from __future__ import annotations

from typing import Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

from src.utils.config import Config


def rewrite_question(original_question: str, retrieved_docs: list[dict[str, Any]] | None = None) -> str:
	"""Return a clarified or expanded version of the original question.

	The LLM should return a single-line rephrased question focused on keywords
	to improve document retrieval.
	"""
	context = "\n\n".join(doc.get("content", "") for doc in (retrieved_docs or []))

	prompt = ChatPromptTemplate.from_messages(
		[
			(
				"system",
				"You are a helpful assistant that rewrites user questions into concise, keyword-rich queries optimized for document retrieval.",
			),
			(
				"human",
				"Original question: {question}\n\nContext (if any):\n{context}\n\nReturn a single improved question aimed at retrieving relevant documents.",
			),
		]
	)

	model_name = Config.get_env_variable("GROQ_MODEL", "llama-3.1-8b-instant")
	llm = ChatGroq(model=model_name, temperature=0.0, groq_api_key=Config.get_groq_api_key())

	messages = prompt.format_messages(question=original_question, context=context)
	resp = llm.invoke(messages)
	new_q = str(resp.content).strip()

	return new_q or original_question

