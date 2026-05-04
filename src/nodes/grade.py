"""Grade an answer for correctness and groundedness using Groq."""

from __future__ import annotations

from typing import Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

from src.utils.config import Config


def grade_answer(question: str, retrieved_docs: list[dict[str, Any]], answer: str) -> str:
	"""Return 'pass' if the answer is grounded and relevant, otherwise 'fail'.

	This function asks the LLM to judge whether `answer` is supported by
	`retrieved_docs` and whether it answers `question`. The LLM must reply
	with exactly `pass` or `fail`.
	"""
	context = "\n\n".join(
		f"Document {i+1}: {doc.get('content','')}" for i, doc in enumerate(retrieved_docs)
	)

	prompt = ChatPromptTemplate.from_messages(
		[
			(
				"system",
				"You are a concise grader. Decide if the provided answer is both grounded in the provided documents and relevant to the question. Reply with exactly: pass or fail.",
			),
			(
				"human",
				"Question: {question}\n\nAnswer: {answer}\n\nContext:\n{context}\n\nRespond with exactly 'pass' or 'fail'.",
			),
		]
	)

	model_name = Config.get_env_variable("GROQ_MODEL", "llama-3.1-8b-instant")

	llm = ChatGroq(model=model_name, temperature=0, groq_api_key=Config.get_groq_api_key())

	messages = prompt.format_messages(question=question, answer=answer, context=context)
	resp = llm.invoke(messages)
	text = str(resp.content).strip().lower()

	if text.startswith("pass"):
		return "pass"
	return "fail"

