# AI Compliance Assistant

---
## Project Overview

The AI Compliance Assistant is a prototype of a retrieval-augmented chatbot designed to assist employees in resolving compliance and policy-related questions within a company.
It combines a local large language model (LLM) served via Ollama (using LLaMA 3.1 8B) with a vector search pipeline (FAISS) for context retrieval.
The agent can:
- Answer questions about internal policies and ethical conduct.
- Provide generative responses with contextual grounding in official documents.
- Retrieve recent reputational risk news via the GDELT API.
- Operate in two modes:

    **🧩 Compliance Assistant — RAG-based**, using indexed company policies and laws.

    **💬 General Chat — generic LLM interaction without RAG retrieval**.

---
##  Project Structure

ai-compliance-agent/
├── app/
│   └── app.py                   # Streamlit interface and chat logic
├── configs/
│   └── config.yaml              # Global configuration (paths, model, parameters)
├── data/
│   ├── policies/                # Internal code of conduct & policies (Markdown)
│   └── laws/                    # External legal summaries (e.g., LGPD)
├── ingestion/
│   ├── ingest.py                # Builds FAISS index from documents
│   └── splitters.py             # Splits text into chunks for embeddings
├── models/
│   ├── embedding.py             # Loads sentence-transformer model
│   └── llm_client.py            # Sends prompts to local Ollama API
├── news/
│   └── gdelt_search.py          # Fetches recent news via GDELT API
├── retrieval/
│   ├── retriever.py             # Handles semantic search with FAISS
│   └── vectordb/                # Stores index + metadata
├── tests/
│   └── test_retriever.py        # Basic smoke test for retriever
├── images/                      # Screenshots for documentation
├── requirements.txt             # Dependencies
├── .gitignore
└── README.md

---
## Project Features

1. **🧠 LLM Integration (Ollama + LLaMA 3.1 8B)**

- Uses Ollama as a local inference server — no external API keys required.
- llm_client.py sends requests to http://localhost:11434/api/generate.
- The LLaMA 3.1 8B model balances speed and accuracy for local prototyping.

2. **🔍 Retrieval-Augmented Generation (RAG)**

- Policies and legal summaries are embedded with sentence-transformers.
- FAISS provides semantic search to retrieve the most relevant text chunks.
- The retrieved context is passed into the LLM prompt to ground its answers.

1. **🧩 Dual Chat Modes**

- Compliance Assistant — cites policies inline (e.g., “(POL-ABAC-002, Art. 12)”).
- General Chat — acts as a general-purpose assistant without RAG retrieval.

4. **🌐 News Integration (GDELT)**

- Fetches and lists recent news headlines related to a company name.
- Uses the GDELT 2.0 API (/api/v2/doc/doc) for open-source news monitoring.
- Can analyze potential reputational risks via the LLM.

5. **🧪 Testing**

- Includes a smoke test (tests/test_retriever.py) to confirm that retrieval runs without crashing.
- The test validates that the FAISS index and metadata load correctly.

---
## ⚙️ System Requirements

- Python ≥ 3.10
- Ollama installed and running locally (`ollama serve`)
- Model downloaded: `ollama pull llama3.1:8b`
- Compatible with macOS, Linux, and Windows (via WSL or local Ollama)

---
## 🔄 Workflow Summary

1.  **Prepare environment**
```
pip install -r requirements.txt
```
2.  **Build vector index**
```
python -m ingestion.ingest
```
3.  **(Optional) Run test**
```
pytest tests/test_retriever.py
```
4.  **Launch app**
```
streamlit run app/app.py
```

---
##  Key Findings

- The combination of local embedding retrieval + LLaMA model provides coherent, policy-grounded answers without relying on paid APIs.
- Inline citations (e.g., “(POL-COC-001, Art. 7)”) are more natural for compliance scenarios than separate citation sections.
- The integration of GDELT adds real-time external context for reputational risk detection.
- The architecture is modular — ingestion, retrieval, and LLM interaction are decoupled for easier maintenance and future scaling.

---
##  Images

App images are saved in the folder `/images`.

---
##  Next Steps

- Integrate LangChain or Agno for richer RAG orchestration and improved prompting.
- Add user authentication and a small audit log for question tracking and governance.
- Optionally deploy via Streamlit Cloud or Docker for easy demonstration and reproducibility.

---
##  Author

André Maccarini 
🔗 [LinkedIn](https://www.linkedin.com/in/amaccarini/) • [Medium](https://medium.com/@andremaccarini) • [Github](https://github.com/andremaccarini)

---
##  License

This project is licensed under the MIT License.