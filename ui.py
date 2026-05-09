"""
Streamlit wrapper that embeds the provided HTML/CSS/JS UI design for the AutoHeal IaC demo.

This file replaces the prior Streamlit-native layout with a direct HTML embed so the
project UI matches the supplied design exactly. Interactive backend wiring can be
added later (e.g. via query endpoints and window.postMessage) if desired.
"""

from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="AutoHeal IaC | AI Command Center", layout="wide")

HTML_UI = r"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AutoHeal IaC | AI Command Center</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/lucide@latest"></script>
    <style>
        body {
            background: radial-gradient(circle at top left, #0d1117, #161b22);
            color: #e6edf3;
            font-family: 'Inter', sans-serif;
            overflow: hidden;
        }
        .glass {
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 16px;
        }
        .neon-text {
            text-shadow: 0 0 10px #00f2ff, 0 0 20px #00f2ff;
        }
        .agent-active {
            border-color: #00f2ff;
            box-shadow: 0 0 15px rgba(0, 242, 255, 0.3);
        }
        pre { font-family: 'Fira Code', monospace; font-size: 0.85rem; }
        .scroll-custom::-webkit-scrollbar { width: 6px; }
        .scroll-custom::-webkit-scrollbar-thumb { background: #30363d; border-radius: 10px; }
    </style>
</head>
<body class="h-screen flex flex-col p-6">

    <!-- Header -->
    <header class="flex justify-between items-center mb-6">
        <div>
            <h1 class="text-2xl font-bold tracking-tighter flex items-center gap-2">
                <i data-lucide="shield-check" class="text-cyan-400"></i>
                AUTOHEAL <span class="text-cyan-400">IaC</span>
            </h1>
            <p class="text-xs text-gray-500 uppercase tracking-widest">Multi-Agent Autonomous Infrastructure</p>
        </div>
        <div class="flex gap-4">
            <button onclick="startHealing()" class="bg-cyan-500 hover:bg-cyan-400 text-black px-6 py-2 rounded-full font-bold transition-all transform hover:scale-105">
                Initiate Healing
            </button>
        </div>
    </header>

    <main class="flex-1 grid grid-cols-12 gap-6 overflow-hidden">
        
        <!-- Left: Status & Agents -->
        <div class="col-span-3 flex flex-col gap-4">
            <div class="glass p-4">
                <h3 class="text-sm font-semibold mb-4 text-gray-400 uppercase">System Pipeline</h3>
                <div id="agent-list" class="space-y-3">
                    <div id="step-1" class="p-3 rounded-lg border border-white/5 flex items-center gap-3 transition-all">
                        <i data-lucide="search" class="w-4 h-4"></i> Verifier Agent
                    </div>
                    <div id="step-2" class="p-3 rounded-lg border border-white/5 flex items-center gap-3 transition-all">
                        <i data-lucide="layers" class="w-4 h-4"></i> Supervisor Agent
                    </div>
                    <div id="step-3" class="p-3 rounded-lg border border-white/5 flex items-center gap-3 transition-all">
                        <i data-lucide="database" class="w-4 h-4"></i> Memory Palace (RAG)
                    </div>
                    <div id="step-4" class="p-3 rounded-lg border border-white/5 flex items-center gap-3 transition-all">
                        <i data-lucide="wand-2" class="w-4 h-4"></i> Healer Agent
                    </div>
                </div>
            </div>

            <div class="glass p-4 flex-1">
                <h3 class="text-sm font-semibold mb-2 text-gray-400 uppercase">Memory Insights</h3>
                <div id="memory-logs" class="text-xs text-cyan-200/70 italic space-y-2">
                    Waiting for execution...
                </div>
            </div>
        </div>

        <!-- Middle: Code Editor Space -->
        <div class="col-span-6 glass flex flex-col overflow-hidden border-t-4 border-t-cyan-500">
            <div class="flex items-center justify-between px-4 py-2 border-b border-white/10 bg-white/5">
                <span class="text-xs font-mono">main.tf</span>
                <span id="status-badge" class="text-[10px] px-2 py-0.5 rounded-full bg-red-500/20 text-red-400 border border-red-500/50">ERRORED</span>
            </div>
            <div class="flex-1 p-4 overflow-auto scroll-custom bg-black/20">
                <pre id="code-display" class="text-gray-400 leading-relaxed">
resource "aws_instance" "web" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t2.micro"

  tags = {
    Name = "Broken-Server
  }
}

resource "aws_s3_bucket" "logs" {
  # Error: Missing required field 'bucket'
}
                </pre>
            </div>
        </div>

        <!-- Right: Terminal Logs -->
        <div class="col-span-3 glass flex flex-col overflow-hidden bg-black/40">
            <div class="px-4 py-2 border-b border-white/10 text-xs font-mono text-gray-500">Terminal Output</div>
            <div id="terminal" class="flex-1 p-4 font-mono text-[11px] space-y-2 overflow-y-auto scroll-custom text-green-500/80">
                <div>> System Ready.</div>
                <div>> Awaiting Terraform scan...</div>
            </div>
        </div>

    </main>

    <script>
        // Initialize Lucide Icons
        lucide.createIcons();

        const logs = [
            { step: 1, text: "> Verifier: Found Syntax Error in main.tf (Line 6)", agent: "step-1" },
            { step: 2, text: "> Supervisor: Classifying as 'Syntax/Missing_Closure'", agent: "step-2" },
            { step: 3, text: "> Memory: Match found in VectorDB (Fix #442)", agent: "step-3", mem: "Retrieved similar fix: Added missing double-quote." },
            { step: 4, text: "> Healer: Applying patch to main.tf...", agent: "step-4" },
            { step: 5, text: "> Final Verifier: Validation Successful. Exit 0.", agent: "" }
        ];

        const fixedCode = `resource "aws_instance" "web" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t2.micro"

  tags = {
    Name = "Healed-Server"
  }
}

resource "aws_s3_bucket" "logs" {
  bucket = "company-logs-production-001"
}`;

        function addTerminalLine(text) {
            const term = document.getElementById('terminal');
            const div = document.createElement('div');
            div.textContent = text;
            term.appendChild(div);
            term.scrollTop = term.scrollHeight;
        }

        async function startHealing() {
            const status = document.getElementById('status-badge');
            
            for (let i = 0; i < logs.length; i++) {
                const item = logs[i];
                
                // Highlight agent
                if(item.agent) {
                    document.querySelectorAll('#agent-list > div').forEach(el => el.classList.remove('agent-active', 'bg-white/10'));
                    const currentAgent = document.getElementById(item.agent);
                    currentAgent.classList.add('agent-active', 'bg-white/10');
                }

                addTerminalLine(item.text);
                
                if(item.mem) {
                    document.getElementById('memory-logs').innerHTML = `<div class="p-2 bg-cyan-500/10 rounded border border-cyan-500/20">${item.mem}</div>`;
                }

                // Simulate processing time
                await new Promise(r => setTimeout(r, 1200));

                if(item.step === 4) {
                    document.getElementById('code-display').textContent = fixedCode;
                    document.getElementById('code-display').classList.replace('text-gray-400', 'text-cyan-300');
                }
            }

            status.textContent = "DEPLOYMENT READY";
            status.classList.replace('bg-red-500/20', 'bg-green-500/20');
            status.classList.replace('text-red-400', 'text-green-400');
            status.classList.replace('border-red-500/50', 'border-green-500/50');
            addTerminalLine("> System fully healed. Infrastructure consistent.");
        }
    </script>
</body>
</html>
"""


def main() -> None:
    st.title("AutoHeal IaC — UI Preview")
    st.markdown("The HTML UI design is embedded below. Use the 'Initiate Healing' button in the UI to simulate the agent workflow.")
    components.html(HTML_UI, height=820, scrolling=True)


if __name__ == "__main__":
    main()

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
