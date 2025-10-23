import sys
from pathlib import Path

# Ensure ROOT is in sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

RETR_PATH = ROOT / "retrieval" / "retriever.py"
CFG_PATH  = ROOT / "configs" / "config.yaml"

# Sanity checks
if not RETR_PATH.exists():
    raise FileNotFoundError(f"retriever.py not found at: {RETR_PATH}")
if not CFG_PATH.exists():
    raise FileNotFoundError(f"config.yaml not found at: {CFG_PATH}")

# Main app
import yaml, streamlit as st
from retrieval.retriever import search, format_citations
from models.llm_client import generate
from news.gdelt_search import search_company_news


CFG = yaml.safe_load(open(CFG_PATH, "r"))

# Streamlit page config
st.set_page_config(page_title="AI Compliance Assistant", page_icon="✅", layout="wide")
st.title("AI Compliance Assistant (Portfolio Prototype)")


with st.sidebar:

    # General settings info
    st.header("Settings")

    # Display LLM and retrieval config
    st.caption("LLM (Ollama)")
    st.text(f"Model: {CFG['llm']['model']}")
    st.caption("Retrieval")
    st.text(f"Embeddings: {CFG['retrieval']['embedding_model']}")
    st.text(f"Top-K: {CFG['retrieval']['top_k']}")
    st.divider()

    # Chat mode selection
    mode = st.selectbox(
        "Chat Mode",
        ["Compliance Assistant", "General Chat"],
        index=0,
        help="Compliance: uses RAG to analyze internal policies and laws. General: general chat, no RAG."
    )

    # Toggle for showing citations as a separate section
    show_citations_section = st.checkbox(
        "Show separate 'Citations' section",
        value=False,
        help="Se desmarcado, as referências aparecem só inline quando necessário."
    )

    # Toggle for developer debug mode (shows retrieved chunks)
    debug_retrieval = st.checkbox("Debug: show retrieved sources", value=False)
    st.divider()

    # ---- News search panel (GDELT integration) ----
    st.caption("News (GDELT)")
    company = st.text_input("Company to monitor", value="Acme Brewing SA")
    timespan = st.selectbox("Timespan", ["7d","14d","30d","90d"], index=2)

    # Fetch news button triggers external API call
    if st.button("Fetch News"):
        with st.spinner("Searching GDELT..."):
            try:
                news = search_company_news(company, timespan=timespan)
            except Exception as e:
                st.error("News search failed.")
                st.caption(f"{e}")
                news = []


        # Display search results or handle empty/limited responses
        if news:
            st.success(f"Found {len(news)} articles")

            # List articles with clickable links
            for a in news:
                st.markdown(f"- [{a['title']}]({a['url']}) — *{a['domain']}*, {a.get('seendate','')}")

            # Optional: run LLM-based reputational risk analysis
            if st.button("Analyze risk on listed articles"):
                bullet_list = "\n".join([f"- {a['title']} ({a['domain']}) — {a['url']}" for a in news])
                prompt = (
                "You are a compliance analyst. Given the following headlines and links, identify potential "
                "reputational risks (e.g., corruption, sanctions, product safety, labor, data breach). "
                "Return a short bullet list of risks with a 0-100 risk score and the cited link per bullet.\n\n"
                f"HEADLINES:\n{bullet_list}"
            )

                # Use local LLM to summarize reputational risks
                risk = generate(prompt, temperature=0.1, system="Be concise and structured.")
                st.markdown("### Risk Analysis")
                st.write(risk)
        else:

            # Handles GDELT rate limits or no-news scenarios
            st.warning("No articles returned. This can happen if GDELT rate-limits (HTTP 429) or if there are no recent results.")
            st.caption("Tips: try a broader timespan (e.g., 90d), fewer records, or alternative spellings (e.g., 'Petrobras' instead of 'Petrobrás').")

import re


# Main chat interface
st.subheader("Chat")

# Initialize chat history (preserved across messages)
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous chat messages
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# Dynamic placeholder changes according to chat mode
placeholder = "Ask about gifts/conflicts/privacy/suppliers..." if mode == "Compliance Assistant" else "Ask me anything..."
user_q = st.chat_input(placeholder)


# ---------------------------------------------------------------------------
# System prompts for different chat behaviors
# ---------------------------------------------------------------------------


SYSTEM_COMPLIANCE = (
    "You are the company's compliance assistant. "
    "Rules:\n"
    "1) Prefer to answer based on the retrieved policy/law excerpts provided (CONTEXT). "
    "2) If the policy is silent, say so and suggest contacting Compliance. "
    "3) Do NOT add a separate 'Citations' section unless explicitly requested. "
    "4) When you rely on a rule, cite it inline in parentheses like (POL-ABAC-002, Art. 12). "
    "5) Keep quotes short when clarifying thresholds/prohibitions."
)
SYSTEM_GENERAL = (
    "You are a helpful and friendly general-purpose assistant. "
    "Be concise, accurate, and practical. Avoid fabrications."
)

# ---------------------------------------------------------------------------
# Helper: respond to capability-related questions
# (e.g., “Can you search the web?”)
# ---------------------------------------------------------------------------

def answer_capabilities_if_asked(q: str) -> str | None:
    q_low = q.lower()
    if re.search(r"\b(search|browse|internet|web|google)\b", q_low):
        return (
            "I don't have full web browsing, but I **can** fetch recent headlines via the **GDELT** news API "
            "(see the sidebar). For policy questions, I use a local knowledge base (policies + law summaries). "
            "If you need a general factual lookup, I can still try to help using my model knowledge."
        )
    return None



# Handle user query
if user_q:
    # Immediately render user message on the screen
    with st.chat_message("user"):
        st.markdown(user_q)
    st.session_state.messages.append({"role": "user", "content": user_q})

    # Generate assistant response
    with st.chat_message("assistant"):
        try:
            if mode == "Compliance Assistant":
                # --- RAG Mode: search policy index for relevant snippets ---
                with st.spinner("Retrieving relevant clauses..."):
                    hits = search(user_q)

                # If no relevant hits, fallback to capability answer or general LLM response
                if not hits:
                    cap = answer_capabilities_if_asked(user_q)
                    fallback = cap or (
                        "I couldn't find a relevant policy excerpt. "
                        "If this is a general question, I can still help without formal citations."
                    )
                    answer = generate(
                        fallback + f"\n\nUser question: {user_q}",
                        temperature=0.3,
                        system=SYSTEM_GENERAL
                    )
                else:

                    # Build context from retrieved snippets
                    context = "\n\n---\n\n".join([h["text"] for h in hits])

                    # Format retrieved metadata for reference
                    cits = format_citations(hits)
                    cite_hint = "; ".join(
                        [f"{c['source']}" + (f" Art. {c['article']}" if c['article'] else "") for c in cits]
                    )

                    # Compose the LLM prompt with context and user question
                    prompt = (
                        f"CONTEXT (policy/law excerpts):\n{context}\n\n"
                        f"Question: {user_q}\n\n"
                        "Answer in a warm, professional tone. "
                        "If you assert a rule, cite it inline like (FILE, Art. X). "
                        "Do not add a separate 'Citations' section unless asked.\n\n"
                        f"Source hint: {cite_hint}"
                    )

                    # Generate the compliance-oriented answer
                    answer = generate(prompt, temperature=0.2, system=SYSTEM_COMPLIANCE)


                    # Optional debug info (shows retrieved chunks)
                    if debug_retrieval:
                        st.markdown("##### Retrieved Sources (debug)")
                        st.code("\n".join([f"- {c['source']}" + (f' — Art. {c['article']}' if c['article'] else '') for c in cits]))
                    # Optional explicit citations section (if checkbox enabled)
                    if show_citations_section and cits:
                        inline_block = "\n".join([f"- {c['source']}" + (f' — Art. {c['article']}' if c['article'] else '') for c in cits])
                        answer += "\n\n**Citations**\n" + inline_block

            else:
                # --- General Chat Mode (no RAG) ---
                cap = answer_capabilities_if_asked(user_q)
                preface = (cap + "\n\n") if cap else ""
                answer = generate(preface + user_q, temperature=0.5, system=SYSTEM_GENERAL)

            # Display the LLM’s response
            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})

        # Catch-all error handler for Ollama/connection issues
        except Exception as e:
            st.error(str(e))
            st.info("Tip: check if Ollama is running and if the model in configs/config.yaml matches one in 'ollama list'.")
