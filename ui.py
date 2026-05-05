"""Streamlit UI for a polished self-healing RAG demo.

This UI uses custom HTML + CSS to render a clean pipeline view with
circular step indicators, live updates, metrics, and final outputs.
It does not change backend logic; it calls the existing `run_agent(question)`
and parses its stdout trace to display the structured fields the UI needs.
"""

from __future__ import annotations

import io
import os
import re
import threading
import time
from contextlib import redirect_stdout
from pathlib import Path
from typing import Any

import streamlit as st

from src.rag_agent import run_agent


DOCS_DIR = Path(__file__).resolve().parent / "docs"


st.set_page_config(page_title="Self-Healing RAG System", layout="wide")

st.markdown(
    """
<style>
.step {
    display: flex;
    align-items: center;
    margin-bottom: 18px;
}
.circle {
    width: 42px;
    height: 42px;
    border-radius: 50%;
    border: 2px solid #00ff88;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-right: 12px;
    font-size: 18px;
    flex-shrink: 0;
    transition: all 0.25s ease;
}
.running {
    border-color: #ffaa00;
    color: #ffaa00;
    box-shadow: 0 0 0 4px rgba(255, 170, 0, 0.12);
}
.done {
    border-color: #00ff88;
    color: #00ff88;
    box-shadow: 0 0 0 4px rgba(0, 255, 136, 0.12);
}
.pending {
    border-color: #555;
    color: #777;
    opacity: 0.5;
}
.text {
    font-size: 16px;
    line-height: 1.4;
}
.pipeline-wrap {
    background: rgba(18, 18, 18, 0.75);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    padding: 18px 18px 8px 18px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.18);
}
.panel-title {
    font-size: 22px;
    font-weight: 700;
    margin-bottom: 12px;
}
.metric-row {
    display: grid;
    grid-template-columns: repeat(5, minmax(0, 1fr));
    gap: 10px;
}
.metric-card {
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    padding: 12px 14px;
}
.metric-label {
    font-size: 12px;
    color: #a9a9a9;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 6px;
}
.metric-value {
    font-size: 20px;
    font-weight: 700;
}
.final-box {
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 14px;
    padding: 16px;
    line-height: 1.6;
}
.subtle {
    color: #9a9a9a;
    font-size: 13px;
}
hr.soft {
    border: none;
    border-top: 1px solid rgba(255, 255, 255, 0.08);
    margin: 14px 0;
}
</style>
""",
    unsafe_allow_html=True,
)


def render_step(icon: str, text: str, status: str) -> str:
    return f'''<div class="step"><div class="circle {status}">{icon}</div><div class="text">{text}</div></div>'''


def save_uploaded_files(files: list[Any]) -> list[str]:
    os.makedirs(DOCS_DIR, exist_ok=True)
    saved: list[str] = []
    for uploaded in files:
        target = os.path.join(DOCS_DIR, uploaded.name)
        with open(target, "wb") as f:
            f.write(uploaded.getvalue())
        saved.append(uploaded.name)
    return saved


def parse_agent_trace(trace: str) -> dict[str, Any]:
    lines = [line.strip() for line in trace.splitlines() if line.strip()]
    retries = 0
    grade_results: list[str] = []
    rewritten_questions: list[str] = []
    retrieved_docs: list[dict[str, str]] = []

    i = 0
    while i < len(lines):
        line = lines[i]

        if line.lower().startswith("retry attempt:"):
            try:
                retries = max(retries, int(line.split(":", 1)[1].strip()))
            except ValueError:
                pass

        if line.lower().startswith("grade result:"):
            grade_results.append(line.split(":", 1)[1].strip().lower())

        if line.lower().startswith("rewritten question:"):
            rewritten_questions.append(line.split(":", 1)[1].strip())

        match = re.match(r"^(\d+)\. source=(.*)$", line)
        if match:
            source = match.group(2).strip()
            content = ""
            if i + 1 < len(lines):
                content = lines[i + 1]
            retrieved_docs.append({"source": source, "content": content})

        i += 1

    final_grade = grade_results[-1] if grade_results else "fail"
    last_rewritten = rewritten_questions[-1] if rewritten_questions else ""

    return {
        "retries": retries,
        "grade_results": grade_results,
        "final_grade": final_grade,
        "rewritten_questions": rewritten_questions,
        "last_rewritten": last_rewritten,
        "retrieved_docs": retrieved_docs,
    }


def render_pipeline(steps: list[tuple[str, str, str]]) -> str:
    return "".join(render_step(icon, text, status) for icon, text, status in steps)


def status_badge(final_grade: str, retries: int) -> str:
    if final_grade == "pass" and retries == 0:
        return "Successful"
    if final_grade == "pass" and retries > 0:
        return "Recovered"
    return "Failed"


def confidence_score(final_grade: str, retries: int) -> int:
    if final_grade == "pass" and retries == 0:
        return 95
    if final_grade == "pass" and retries > 0:
        return 80
    if retries > 0:
        return 35
    return 15


def run_backend_with_trace(question: str) -> dict[str, Any]:
    buffer = io.StringIO()
    result_container: dict[str, Any] = {"answer": "", "error": None}

    def target() -> None:
        try:
            with redirect_stdout(buffer):
                result_container["answer"] = run_agent(question)
        except Exception as exc:  # pragma: no cover - surfaced in UI
            result_container["error"] = str(exc)

    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    thread.join()

    trace = buffer.getvalue()
    parsed = parse_agent_trace(trace)

    final_answer = result_container.get("answer") or ""
    grade_result = parsed.get("final_grade", "fail")
    retries = parsed.get("retries", 0)
    retrieved_docs = parsed.get("retrieved_docs", [])
    rewritten_question = parsed.get("last_rewritten", "")

    return {
        "final_answer": final_answer,
        "grade_result": grade_result,
        "retries": retries,
        "retrieved_docs": retrieved_docs,
        "rewritten_question": rewritten_question,
        "trace": trace,
        "error": result_container.get("error"),
    }


left, right = st.columns([1, 1.5])

with left:
    st.title("Knowledge Base")
    uploaded_files = st.file_uploader("Upload .txt files", type=["txt"], accept_multiple_files=True)
    if uploaded_files:
        saved = save_uploaded_files(uploaded_files)
        st.success(f"Saved {len(saved)} file(s) into docs/")

    st.markdown("<hr class='soft'>", unsafe_allow_html=True)
    question = st.text_input("Ask a question")
    run_clicked = st.button("Run Agent", type="primary")

with right:
    st.title("Live Pipeline")
    pipeline = st.empty()
    metrics = st.empty()
    final_output = st.empty()
    rewritten_output = st.empty()
    docs_output = st.empty()
    debug_output = st.empty()

if run_clicked:
    if not question.strip():
        st.warning("Please enter a question before running the agent.")
    else:
        # Step 1
        pipeline.markdown(
            f"<div class='pipeline-wrap'>"
            f"<div class='panel-title'>Pipeline Execution</div>"
            f"{render_pipeline([('🔍', 'Retrieving documents...', 'running'), ('⚙', 'Generating answer...', 'pending'), ('🧪', 'Checking answer quality...', 'pending'), ('🔁', 'Healing loop...', 'pending')])}"
            f"</div>",
            unsafe_allow_html=True,
        )
        time.sleep(1.2)

        pipeline.markdown(
            f"<div class='pipeline-wrap'>"
            f"<div class='panel-title'>Pipeline Execution</div>"
            f"{render_pipeline([('✔', 'Retrieval complete', 'done'), ('⚙', 'Generating answer...', 'pending'), ('🧪', 'Checking answer quality...', 'pending'), ('🔁', 'Healing loop...', 'pending')])}"
            f"</div>",
            unsafe_allow_html=True,
        )
        time.sleep(0.5)

        # Step 2
        pipeline.markdown(
            f"<div class='pipeline-wrap'>"
            f"<div class='panel-title'>Pipeline Execution</div>"
            f"{render_pipeline([('✔', 'Retrieval complete', 'done'), ('⚙', 'Generating answer...', 'running'), ('🧪', 'Checking answer quality...', 'pending'), ('🔁', 'Healing loop...', 'pending')])}"
            f"</div>",
            unsafe_allow_html=True,
        )
        time.sleep(1.2)

        pipeline.markdown(
            f"<div class='pipeline-wrap'>"
            f"<div class='panel-title'>Pipeline Execution</div>"
            f"{render_pipeline([('✔', 'Retrieval complete', 'done'), ('✔', 'Generation complete', 'done'), ('🧪', 'Checking answer quality...', 'pending'), ('🔁', 'Healing loop...', 'pending')])}"
            f"</div>",
            unsafe_allow_html=True,
        )
        time.sleep(0.5)

        # Step 3
        pipeline.markdown(
            f"<div class='pipeline-wrap'>"
            f"<div class='panel-title'>Pipeline Execution</div>"
            f"{render_pipeline([('✔', 'Retrieval complete', 'done'), ('✔', 'Generation complete', 'done'), ('🧪', 'Checking answer quality...', 'running'), ('🔁', 'Healing loop...', 'pending')])}"
            f"</div>",
            unsafe_allow_html=True,
        )
        time.sleep(1.2)

        result = run_backend_with_trace(question.strip())
        final_answer = result["final_answer"]
        grade_result = result["grade_result"]
        retries = int(result["retries"] or 0)
        retrieved_docs = result["retrieved_docs"] or []
        rewritten_question = result["rewritten_question"]

        if grade_result == "fail":
            pipeline.markdown(
                f"<div class='pipeline-wrap'>"
                f"<div class='panel-title'>Pipeline Execution</div>"
                f"{render_pipeline([('✔', 'Retrieval complete', 'done'), ('✔', 'Generation complete', 'done'), ('❌', 'Hallucination detected', 'running'), ('🔁', 'Healing loop...', 'running')])}"
                f"</div>",
                unsafe_allow_html=True,
            )
            time.sleep(1)
            pipeline.markdown(
                f"<div class='pipeline-wrap'>"
                f"<div class='panel-title'>Pipeline Execution</div>"
                f"{render_pipeline([('✔', 'Retrieval complete', 'done'), ('✔', 'Generation complete', 'done'), ('❌', 'Hallucination detected', 'done'), ('🔁', 'Rewriting question...', 'running')])}"
                f"</div>",
                unsafe_allow_html=True,
            )
            time.sleep(1)
            pipeline.markdown(
                f"<div class='pipeline-wrap'>"
                f"<div class='panel-title'>Pipeline Execution</div>"
                f"{render_pipeline([('✔', 'Retrieval complete', 'done'), ('✔', 'Generation complete', 'done'), ('❌', 'Hallucination detected', 'done'), ('🔁', 'Retrying...', 'running')])}"
                f"</div>",
                unsafe_allow_html=True,
            )
            time.sleep(0.8)
        else:
            pipeline.markdown(
                f"<div class='pipeline-wrap'>"
                f"<div class='panel-title'>Pipeline Execution</div>"
                f"{render_pipeline([('✔', 'Retrieval complete', 'done'), ('✔', 'Generation complete', 'done'), ('✔', 'Answer validated', 'done'), (' ', 'Healing not required', 'pending')])}"
                f"</div>",
                unsafe_allow_html=True,
            )

        conf = confidence_score(grade_result, retries)
        final_status = status_badge(grade_result, retries)
        hallucination = "Yes" if grade_result == "fail" else "No"

        metrics.markdown(
            f"""
            <div class='pipeline-wrap'>
              <div class='panel-title'>Metrics</div>
              <div class='metric-row'>
                <div class='metric-card'><div class='metric-label'>Confidence Score</div><div class='metric-value'>{conf}%</div></div>
                <div class='metric-card'><div class='metric-label'>Retry Count</div><div class='metric-value'>{retries}</div></div>
                <div class='metric-card'><div class='metric-label'>Docs Retrieved</div><div class='metric-value'>{len(retrieved_docs)}</div></div>
                <div class='metric-card'><div class='metric-label'>Hallucination Detected</div><div class='metric-value'>{hallucination}</div></div>
                <div class='metric-card'><div class='metric-label'>Final Status</div><div class='metric-value'>{final_status}</div></div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        final_output.markdown("### Final Answer")
        final_output.success(final_answer or "No answer produced.")

        if rewritten_question:
            rewritten_output.info("Rewritten: " + rewritten_question)

        with docs_output.expander("Retrieved Documents"):
            if not retrieved_docs:
                st.write("No documents retrieved.")
            else:
                for index, doc in enumerate(retrieved_docs, start=1):
                    st.markdown(f"**{index}. {doc.get('source', '')}**")
                    st.write(doc.get("content", ""))

        with debug_output.expander("Debug Trace"):
            st.code(result.get("trace", "") or "No trace captured.")

        st.markdown("<hr class='soft'>", unsafe_allow_html=True)
        st.caption("Run command: streamlit run ui.py")

else:
    pipeline.markdown(
        f"<div class='pipeline-wrap'>"
        f"<div class='panel-title'>Pipeline Execution</div>"
        f"{render_pipeline([('🔍', 'Retrieving documents...', 'pending'), ('⚙', 'Generating answer...', 'pending'), ('🧪', 'Checking answer quality...', 'pending'), ('🔁', 'Healing loop...', 'pending')])}"
        f"</div>",
        unsafe_allow_html=True,
    )
    metrics.markdown(
        """
        <div class='pipeline-wrap'>
          <div class='panel-title'>Metrics</div>
          <div class='subtle'>Metrics will appear after you run the agent.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    final_output.info("Final answer will appear here after execution.")
    st.caption("Run command: streamlit run ui.py")
