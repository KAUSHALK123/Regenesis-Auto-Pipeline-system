"""Streamlit UI for the self-healing RAG system."""

from __future__ import annotations

import io
import re
from contextlib import redirect_stdout
from pathlib import Path
from typing import Any

import streamlit as st

from src.rag_agent import run_agent


DOCS_DIR = Path(__file__).resolve().parent / "docs"


def save_uploaded_files(files: list[Any]) -> list[str]:
    """Save uploaded .txt files into the docs folder and return saved names."""
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    saved_files: list[str] = []

    for uploaded in files:
        target_path = DOCS_DIR / uploaded.name
        target_path.write_bytes(uploaded.getvalue())
        saved_files.append(uploaded.name)

    return saved_files


def parse_agent_trace(trace: str) -> dict[str, Any]:
    """Parse stdout trace from run_agent for retries, rewrites, grades and docs."""
    lines = [line.strip() for line in trace.splitlines() if line.strip()]

    retries = 0
    rewritten_questions: list[str] = []
    grade_results: list[str] = []
    retrieved_docs: list[dict[str, str]] = []

    idx = 0
    while idx < len(lines):
        line = lines[idx]

        if line.startswith("Retry attempt:"):
            try:
                retries = max(retries, int(line.split(":", 1)[1].strip()))
            except ValueError:
                pass

        if line.startswith("Rewritten question:"):
            rewritten_questions.append(line.split(":", 1)[1].strip())

        if line.startswith("Grade result:"):
            grade_results.append(line.split(":", 1)[1].strip().lower())

        source_match = re.match(r"^\d+\. source=(.*)$", line)
        if source_match:
            content = ""
            if idx + 1 < len(lines):
                content = lines[idx + 1]
            retrieved_docs.append(
                {
                    "source": source_match.group(1).strip(),
                    "content": content,
                }
            )

        idx += 1

    final_grade = grade_results[-1] if grade_results else "fail"
    last_rewritten = rewritten_questions[-1] if rewritten_questions else ""

    return {
        "retries": retries,
        "rewritten_questions": rewritten_questions,
        "last_rewritten": last_rewritten,
        "grade_results": grade_results,
        "final_grade": final_grade,
        "retrieved_docs": retrieved_docs,
    }


def main() -> None:
    """Render the Streamlit app."""
    st.set_page_config(page_title="Self-Healing RAG System", page_icon="🛠️", layout="centered")

    st.title("Self-Healing RAG System")
    st.write("Upload .txt files, ask a question, and watch the self-healing RAG flow.")

    uploaded_files = st.file_uploader(
        "Upload knowledge files (.txt)",
        type=["txt"],
        accept_multiple_files=True,
    )

    if uploaded_files:
        saved_names = save_uploaded_files(uploaded_files)
        st.success(f"Saved {len(saved_names)} file(s) to docs/: {', '.join(saved_names)}")

    question = st.text_input("Ask a question")

    if st.button("Run Agent", type="primary"):
        if not question.strip():
            st.warning("Please enter a question first.")
            st.stop()

        with st.status("Running self-healing workflow...", expanded=True) as status:
            status.write("🔍 Retrieving documents...")
            status.write("🤖 Generating answer...")
            status.write("🧪 Checking answer quality...")

            trace_buffer = io.StringIO()
            with redirect_stdout(trace_buffer):
                final_answer = run_agent(question.strip())

            trace = trace_buffer.getvalue()
            parsed = parse_agent_trace(trace)

            if parsed["retries"] > 0:
                for _ in range(parsed["retries"]):
                    status.write("❌ Hallucination detected!")
                    status.write("🔁 Rewriting question...")
                    status.write("🔄 Retrying...")

            if parsed["final_grade"] == "pass":
                status.write("✅ Answer validated")
            elif final_answer == "I don't know":
                status.write("⚠️ Max retries reached. Returning safe fallback.")
            else:
                status.write("⚠️ Answer could not be validated confidently.")

            status.update(label="Run complete", state="complete", expanded=False)

        st.subheader("Final Answer")
        st.write(final_answer)

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Retries", parsed["retries"])
        with col2:
            st.metric("Final Grade", parsed["final_grade"])

        if parsed["last_rewritten"]:
            st.subheader("Rewritten Question")
            st.write(parsed["last_rewritten"])

        if parsed["retrieved_docs"]:
            with st.expander("Retrieved Documents", expanded=False):
                for i, doc in enumerate(parsed["retrieved_docs"], start=1):
                    st.markdown(f"**{i}.** {doc['source']}")
                    st.write(doc["content"])

        with st.expander("Debug Trace", expanded=False):
            st.code(trace if trace else "No trace output captured.")

    st.caption("Run command: streamlit run ui.py")


if __name__ == "__main__":
    main()
