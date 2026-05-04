"""Minimal LangGraph-based RAG agent."""

from __future__ import annotations

from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from src.nodes.generate import generate_answer
from src.nodes.retrieve import retrieve_documents
from src.nodes.grade import grade_answer
from src.nodes.rewrite import rewrite_question
from src.utils.logger import logger


class RAGState(TypedDict):
	"""State shared across the retrieval, generation, grading and healing steps."""

	question: str
	retrieved_docs: list[dict]
	answer: str
	grade_result: str
	retries: int


def retrieve_node(state: RAGState) -> dict:
	"""Retrieve the top documents for the incoming question."""
	retrieved_docs = retrieve_documents(state["question"], top_k=3)

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

	return {"retrieved_docs": retrieved_docs}


def generate_node(state: RAGState) -> dict:
	"""Generate the final answer from the retrieved documents."""
	answer = generate_answer(state["question"], state.get("retrieved_docs", []))

	print("Final answer:")
	print(answer)

	return {"answer": answer}


def grade_node(state: RAGState) -> dict:
	"""Grade the generated answer and return pass/fail."""
	grade = grade_answer(state["question"], state.get("retrieved_docs", []), state.get("answer", ""))
	print(f"Grade result: {grade}")
	return {"grade_result": grade}


def build_graph():
	"""Build the simple START -> retrieve -> generate -> END graph."""
	graph = StateGraph(RAGState)
	graph.add_node("retrieve", retrieve_node)
	graph.add_node("generate", generate_node)
	graph.add_node("grade", grade_node)
	graph.add_edge(START, "retrieve")
	graph.add_edge("retrieve", "generate")
	graph.add_edge("generate", "grade")
	graph.add_edge("grade", END)
	return graph.compile()


rag_graph = build_graph()


def run_agent(question: str) -> str:
	"""Run the LangGraph RAG workflow for a single question."""
	# Initialize state
	state = {"question": question, "retrieved_docs": [], "answer": "", "grade_result": "", "retries": 0}

	while True:
		result = rag_graph.invoke(state)
		# Update state with results from the graph
		state.update(result)

		grade = state.get("grade_result", "fail")
		if grade == "pass":
			return state.get("answer", "")

		# Failed grading path
		state["retries"] = state.get("retries", 0) + 1
		print(f"Retry attempt: {state['retries']}")

		if state["retries"] > 2:
			print("Exceeded retry limit. Returning: I don't know")
			return "I don't know"

		# Rewrite question and retry
		new_q = rewrite_question(state["question"], state.get("retrieved_docs", []))
		print(f"Rewritten question: {new_q}")
		state["question"] = new_q
		# loop will invoke graph again


def run_rag(question: str) -> str:
	"""Backward-compatible wrapper for the graph-based agent."""
	return run_agent(question)


if __name__ == "__main__":
	try:
		user_question = input("Ask a question: ").strip()
		if not user_question:
			logger.error("No question provided.")
		else:
			run_agent(user_question)
	except Exception as exc:
		logger.error("RAG pipeline failed: %s", exc, exc_info=True)
