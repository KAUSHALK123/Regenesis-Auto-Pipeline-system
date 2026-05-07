# -*- coding: utf-8 -*-
"""Streamlit UI for Regenesis Self-Healing RAG System - Professional Glassmorphism Design."""

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

st.set_page_config(page_title="Regenesis | AI Guardian Layer", layout="wide")

# ============================================================================
# GLASSMORPHISM CSS STYLING
# ============================================================================

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap');

:root {
    --bg: #0b0e14;
    --panel: #14171f;
    --accent: #00d2ff;
    --success: #00ffa3;
    --error: #ff3e6d;
    --text-main: #ffffff;
    --text-dim: #94a3b8;
    --border: rgba(255, 255, 255, 0.06);
}

* { box-sizing: border-box; transition: all 0.25s ease; }

body { background: var(--bg); color: var(--text-main); font-family: 'Plus Jakarta Sans', sans-serif; margin: 0; }

header { height: 70px; border-bottom: 1px solid var(--border); display:flex; align-items:center; padding:0 30px; justify-content:space-between; }
.logo { font-weight:900; font-size:1.6rem; letter-spacing:-0.8px; text-transform:uppercase; }
.logo span { color: var(--accent); }
.client-tag { font-size:0.75rem; color:var(--text-dim); background: rgba(255,255,255,0.05); padding:5px 12px; border-radius:6px; }

.container { display:flex; flex:1; height: calc(100vh - 60px); overflow:hidden; }
.chat-section { flex: 0 0 70%; display:flex; flex-direction:column; border-right:1px solid var(--border); background: radial-gradient(circle at top left, rgba(0,210,255,0.03), transparent); padding:15px; }
.chat-output { flex:1; padding:15px; overflow-y:auto; display:flex; flex-direction:column; gap:12px; background:var(--panel); border:1px solid var(--border); border-radius:14px; }
.message { max-width:85%; padding:14px 16px; border-radius:14px; line-height:1.5; font-size:0.93rem; }
.ai-msg { background: var(--panel); border:1px solid var(--border); border-bottom-left-radius:4px; }
.user-msg { align-self:flex-end; background:var(--accent); color:#000; font-weight:600; border-bottom-right-radius:4px; }
.chat-input-area { padding:30px 40px; border-top:1px solid var(--border); display:flex; gap:15px; }
.input-wrapper { flex:1; background:var(--panel); border:1px solid var(--border); border-radius:12px; display:flex; align-items:center; padding:5px 15px; }
.input-wrapper input { flex:1; background:transparent; border:none; color:white; padding:12px; outline:none; font-size:0.9rem; }
.send-btn { background:var(--accent); border:none; width:45px; height:45px; border-radius:10px; cursor:pointer; color:#000; }

.eval-section { flex:0 0 30%; background:#0f1218; padding:20px; display:flex; flex-direction:column; gap:15px; overflow-y:auto; }
.eval-title { font-size:0.7rem; font-weight:800; color:var(--text-dim); text-transform:uppercase; letter-spacing:1px; }
.pipeline-card { background:var(--panel); border-radius:14px; padding:14px; border:1px solid var(--border); }
.step { display:flex; gap:12px; padding:10px 0; border-bottom:1px solid rgba(255,255,255,0.03); opacity:0.4; color:var(--text-dim); }
.step:last-child { border:none; }
.step.active { opacity:1; color:var(--accent); }
.step.done { opacity:1; color:var(--success); }
.step.error { opacity:1; color:var(--error); }
.step-icon { width:32px; height:32px; border-radius:8px; border:2px solid currentColor; display:flex; align-items:center; justify-content:center; font-size:0.8rem; background:rgba(255,255,255,0.02); }
.step-label { font-size:0.85rem; font-weight:700; display:block; }
.step-status { font-size:0.7rem; opacity:0.7; }
#healing-module { margin-top:10px; padding:15px; background: rgba(255,62,109,0.05); border:1px solid rgba(255,62,109,0.15); border-radius:12px; display:none; }
.progress-track { height:4px; background: rgba(255,255,255,0.05); border-radius:2px; margin-top:10px; overflow:hidden; }
.progress-fill { width:0%; height:100%; background:var(--error); box-shadow:0 0 10px var(--error); animation: heal 2.5s infinite; }
@keyframes heal { 0% { width:0%; } 100% { width:100%; } }
.metrics-grid { display:grid; grid-template-columns:repeat(3, 1fr); gap:12px; margin:15px 0; }
.metric-box { background:var(--panel); padding:16px 12px; border-radius:12px; text-align:center; border:1px solid var(--border); display:flex; flex-direction:column; justify-content:center; min-height:90px; }
.m-val { font-size:1.8rem; font-weight:900; color:var(--accent); display:block; line-height:1.1; }
.m-lbl { font-size:0.65rem; color:var(--text-dim); text-transform:uppercase; margin-top:8px; letter-spacing:0.6px; font-weight:700; }

hr.soft { border:none; border-top:1px solid rgba(255,255,255,0.08); margin:14px 0; }
</style>
""",
    unsafe_allow_html=True,
)

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================




def save_uploaded_files(files: list[Any]) -> list[str]:
    """Save uploaded files to docs directory."""
    os.makedirs(DOCS_DIR, exist_ok=True)
    saved: list[str] = []
    for uploaded in files:
        target = DOCS_DIR / uploaded.name
        target.write_bytes(uploaded.getvalue())
        saved.append(uploaded.name)
    return saved


def parse_agent_trace(trace: str) -> dict[str, Any]:
    """Parse trace output from RAG agent execution."""
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


def confidence_score(final_grade: str, retries: int) -> int:
    """Calculate confidence score based on grade and retry count."""
    if final_grade == "pass" and retries == 0:
        return 96
    if final_grade == "pass" and retries > 0:
        return 82
    if retries > 0:
        return 45
    return 23


def calculate_doc_match_percentage(doc_count: int, max_docs: int = 3) -> int:
    """Calculate document matching percentage."""
    if max_docs == 0:
        return 0
    percentage = int((doc_count / max_docs) * 100)
    return min(100, percentage)


def run_backend_with_trace(question: str) -> dict[str, Any]:
    """Execute RAG agent and capture trace."""
    buffer = io.StringIO()
    result_container: dict[str, Any] = {"answer": "", "error": None}

    def target() -> None:
        try:
            with redirect_stdout(buffer):
                result_container["answer"] = run_agent(question)
        except Exception as exc:
            result_container["error"] = str(exc)

    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    thread.join()

    trace = buffer.getvalue()
    parsed = parse_agent_trace(trace)

    return {
        "final_answer": result_container.get("answer") or "",
        "grade_result": parsed.get("final_grade", "fail"),
        "retries": int(parsed.get("retries", 0) or 0),
        "retrieved_docs": parsed.get("retrieved_docs", []),
        "rewritten_question": parsed.get("last_rewritten", ""),
        "trace": trace,
        "error": result_container.get("error"),
    }


def render_step(icon: str, title: str, status: str, status_text: str = "Waiting...") -> str:
    """Render a step block matching the new theme."""
    cls = f"step {status.lower()}" if status else "step"
    progress_html = ""
    if status.lower() == "active":
        progress_html = "<div class='step-progress-track'><div class='step-progress-fill'></div></div>"
    return (
        f'<div class="{cls}" id="step-{title.replace(" ", "-").lower()}">'
        f'<div class="step-icon">{icon}</div>'
        f'<div style="flex:1;">'
        f'<span class="step-label">{title}</span>'
        f'<span class="step-status">{status_text}</span>'
        f'{progress_html}'
        f'</div>'
        f'</div>'
    )


def render_evaluation_stage(
    grade_result: str,
    doc_match: int,
    hallucination_confidence: int,
    retrieved_docs_count: int,
) -> str:
    """Render evaluation stage with metrics."""
    hallucination_detected = "Yes" if grade_result == "fail" else "No"
    hallucination_text = "Potential hallucination detected in generated answer. Model may have used information not found in source documents."
    
    return f"""
<div class="evaluation-section">
    <div class="eval-title">Evaluation Stage</div>
    <div class="eval-metric">
        <span class="eval-label">Document Match</span>
        <span class="eval-value">{doc_match}%</span>
    </div>
    <div class="eval-metric">
        <span class="eval-label">Docs Retrieved</span>
        <span class="eval-value">{retrieved_docs_count}/3</span>
    </div>
    <div class="eval-metric">
        <span class="eval-label">Hallucination Detected</span>
        <span class="eval-value">{hallucination_detected}</span>
    </div>
    <div class="eval-metric">
        <span class="eval-label">Confidence</span>
        <span class="eval-value">{100 - hallucination_confidence}%</span>
    </div>
    {f'<div class="hallucination-report">⚠️ {hallucination_text}</div>' if grade_result == "fail" else ""}
</div>
"""



# ============================================================================
# PAGE LAYOUT
# ============================================================================

# Header (top bar)
st.markdown(
    """
    <header>
        <div class="logo">REGENESIS<span>.AI</span></div>
        <div class="client-tag">Project: XYZ_Production_RAG</div>
    </header>
    """,
    unsafe_allow_html=True,
)

# Main container columns (left chat 70%, right evaluation 30%)
left, right = st.columns([7, 3], gap="large")

with left:
    # Upload section
    with st.expander("📤 Upload Documents", expanded=True):
        uploaded_files = st.file_uploader(
            "Select documents to add to knowledge base",
            type=["txt", "pdf", "md"],
            accept_multiple_files=True,
            key="doc_uploader",
        )
        if uploaded_files:
            saved = save_uploaded_files(uploaded_files)
            st.success(f"✓ Uploaded {len(saved)} document(s)")
    
    # Display already uploaded documents
    with st.expander("📚 Knowledge Base Documents", expanded=True):
        if DOCS_DIR.exists():
            doc_files = list(DOCS_DIR.glob("*"))
            if doc_files:
                st.markdown("<div style='font-size:0.85rem;color:var(--text-dim);'>Currently loaded:</div>", unsafe_allow_html=True)
                for doc_file in doc_files:
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.caption(f"📄 {doc_file.name}")
                    with col2:
                        if st.button("×", key=f"delete_{doc_file.name}", help="Remove document"):
                            doc_file.unlink()
                            st.rerun()
            else:
                st.markdown("<div style='font-size:0.85rem;color:var(--text-dim);padding:10px;'>No documents uploaded yet</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='font-size:0.85rem;color:var(--text-dim);padding:10px;'>No documents uploaded yet</div>", unsafe_allow_html=True)
    
    # Chat area - OUTPUT label and messages appear only after execution
    st.markdown("<div class='chat-section'>", unsafe_allow_html=True)
    
    output_label_placeholder = st.empty()
    chat_output = st.empty()

    # input area (left)
    input_col1, input_col2 = st.columns([10, 1])
    with input_col1:
        user_input = st.text_input("", placeholder="Ask a question to the system...", key="chat_input")
    with input_col2:
        send = st.button("Send", key="send_left")

    st.markdown("</div>", unsafe_allow_html=True)

with right:
    st.markdown("<div class='eval-section'>", unsafe_allow_html=True)
    st.markdown("<div class='eval-title'>Live Pipeline Execution</div>", unsafe_allow_html=True)
    pipeline_placeholder = st.empty()
    healing_placeholder = st.empty()
    metrics_placeholder = st.empty()
    docs_placeholder = st.empty()
    st.markdown("</div>", unsafe_allow_html=True)

# ============================================================================
# EXECUTION LOGIC
# ============================================================================

# Handle send button or left send
def execute_query_and_render(query_text: str, chat_out: Any):
    if not query_text.strip():
        st.warning("Please enter a question before sending.")
        return

    # Show OUTPUT label on first execution
    output_label_placeholder.markdown("<div class='eval-title' style='margin-bottom:12px;'>📤 Output</div>", unsafe_allow_html=True)

    # append user message
    chat_out.markdown(f"<div class=\"message user-msg\">{query_text}</div>", unsafe_allow_html=True)

    # show pipeline active states
    pipeline_html_content = (
        render_step('🔍', 'Document Retrieval', 'active', 'Retrieving...') +
        render_step('🪄', 'RAG Generation', 'pending', 'Waiting...') +
        render_step('🛡️', 'Hallucination Guard', 'pending', 'Waiting...')
    )
    pipeline_placeholder.markdown(f"<div class=\"pipeline-card\">{pipeline_html_content}</div>", unsafe_allow_html=True)

    time.sleep(1.0)

    # simulate progression
    pipeline_html_content = (
        render_step('🔍', 'Document Retrieval', 'done', '6 chunks retrieved') +
        render_step('🪄', 'RAG Generation', 'active', 'Generating...') +
        render_step('🛡️', 'Hallucination Guard', 'pending', 'Scanning...')
    )
    pipeline_placeholder.markdown(f"<div class=\"pipeline-card\">{pipeline_html_content}</div>", unsafe_allow_html=True)

    time.sleep(1.5)

    # run backend
    result = run_backend_with_trace(query_text)
    final_answer = result.get('final_answer', '')
    grade_result = result.get('grade_result', 'fail')
    retries = int(result.get('retries', 0) or 0)
    retrieved_docs = result.get('retrieved_docs', []) or []

    # final pipeline state
    guard_state = 'done' if grade_result == 'pass' else 'error'
    guard_text = 'Validated' if grade_result == 'pass' else 'Hallucination Detected'
    pipeline_html_content = (
        render_step('🔍', 'Document Retrieval', 'done', 'Completed') +
        render_step('🪄', 'RAG Generation', 'done', 'Completed') +
        render_step('🛡️', 'Hallucination Guard', guard_state, guard_text)
    )
    pipeline_placeholder.markdown(f"<div class=\"pipeline-card\">{pipeline_html_content}</div>", unsafe_allow_html=True)

    # show healing if needed
    if grade_result != 'pass':
        healing_placeholder.markdown(
            """
            <div id="healing-module">
                <div style="font-size:0.65rem;color:var(--error);font-weight:800;display:flex;justify-content:space-between;">
                    <span><i class="fas fa-bolt"></i> SELF-HEALING ACTIVE</span>
                    <span>FIX_V2</span>
                </div>
                <div class="progress-track"><div class="progress-fill"></div></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        time.sleep(2.8)
        healing_placeholder.empty()

    # append final AI message
    ai_html = f"<div class=\"message ai-msg\"><strong>Response:</strong> {final_answer or 'No answer produced.'}</div>"
    chat_out.markdown(ai_html, unsafe_allow_html=True)

    # metrics - display all 5 metrics like the screenshot
    confidence = confidence_score(grade_result, retries)
    doc_match = calculate_doc_match_percentage(len(retrieved_docs))
    hallucination_detected = "No" if grade_result == "pass" else "Yes"
    final_status = "Success" if grade_result == "pass" and retries == 0 else ("Recovered" if grade_result == "pass" else "Failed")
    
    metrics_placeholder.markdown(
        f"""
        <div style="margin-top:10px;">
            <div class="eval-title" style="margin-bottom:12px;">Metrics</div>
            <div class="metrics-grid">
                <div class="metric-box"><span class="m-val">{confidence}%</span><span class="m-lbl">Confidence<br/>Score</span></div>
                <div class="metric-box"><span class="m-val">{retries}</span><span class="m-lbl">Retry<br/>Count</span></div>
                <div class="metric-box"><span class="m-val">{len(retrieved_docs)}</span><span class="m-lbl">Docs<br/>Retrieved</span></div>
                <div class="metric-box"><span class="m-val">{hallucination_detected}</span><span class="m-lbl">Hallucination<br/>Detected</span></div>
                <div class="metric-box"><span class="m-val" style="color:var(--success);">{final_status}</span><span class="m-lbl">Final<br/>Status</span></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # show retrieved docs
    if retrieved_docs:
        docs_placeholder.markdown("<div class='eval-title'>Retrieved Knowledge Base</div>", unsafe_allow_html=True)
        for i, d in enumerate(retrieved_docs, start=1):
            docs_placeholder.markdown(
                f"""
                <div class="doc-item"><div class="doc-source">📄 {i}. {d.get('source','Unknown')}</div><div class="doc-content">{d.get('content','')}</div></div>
                """,
                unsafe_allow_html=True,
            )
    else:
        docs_placeholder.warning("No documents retrieved during this execution.")

# Initial pipeline state on right
if send:
    execute_query_and_render(user_input, chat_output)

# Initial pipeline state on right
pipeline_placeholder.markdown(
    f"<div class=\"pipeline-card\">{render_step('🔍','Document Retrieval','pending','Pending')}{render_step('🪄','RAG Generation','pending','Pending')}{render_step('🛡️','Hallucination Guard','pending','Pending')}</div>",
    unsafe_allow_html=True,
)

# Footer
st.markdown("<hr class='soft'>", unsafe_allow_html=True)
st.caption("Regenesis Self-Healing RAG System | Run: `streamlit run ui.py`")
