# 🚀 XIPO - Explainable IPOs

**XIPO** is an end-to-end AI-powered pipeline that automates due diligence for upcoming IPOs. It eliminates the 4-8 hours of manual research by automating the discovery, extraction, and analysis of Prospectus filings.

XIPO combines **deterministic rule-based agents** for 100% financial accuracy with **LLMs** for semantic synthesis, ensuring zero hallucination on critical data.

---

## 💡 Why XIPO? (The "Why Not ChatGPT?" Analysis)

While ChatGPT is powerful, it has fundamental limitations for financial due diligence:

| Challenge | ChatGPT Limitation | XIPO Solution |
|---|---|---|
| **Financial Accuracy** | LLMs hallucinate numbers — they misread parentheses, FY labels, and decimal points. | **Deterministic extraction** via regex ensures 100% accuracy — zero LLM hallucination on financials. |
| **Table Extraction** | LLMs struggle with complex multi-column financial tables in PDFs. | **pdfplumber** extracts tables with row/column structure preserved reliably. |
| **Document Size** | 300+ page filings often exceed context limits or cause "Lost in the Middle" errors. | **Map-Reduce** splits documents into sections, processing each independently for full coverage. |
| **Real-time News** | ChatGPT's data is stale. It can't access news from the last few days. | **Direct scraping** of the latest news with time-decay weighted sentiment analysis. |
| **Auditability** | No source citation — you can't verify where a number came from. | Our RAG chatbot cites **exact page numbers** for every answer. |

---

## 🚀 Key Features

- 🌐 **Automated Scraper**: Automatically finds and downloads the latest filings from official regulatory databases.
- 📊 **Metric Extraction**: Regex-based extraction of Revenue, PAT, EBITDA, EPS, and 15+ other key indicators.
- 💬 **RAG Chatbot**: "Chat with the Prospectus" using FAISS vector search with exact page citations.
- 📝 **Investment Memo**: Multi-stage Map-Reduce pipeline (Llama 3.3-70b via Cerebras) for institutional-grade reports.
- 📈 **Visual Analytics**: Interactive Plotly financial visualizations (Revenue, PAT, Margins, etc.).
- 📰 **Sentiment Engine Engine**: Sentiment analysis of the latest news articles with LLM-powered semantic nuance.

---

## 🏗️ Architecture & Pipeline Stages

### ⚙️ The 11-Stage Pipeline
1. **Discovery**: Scrapes regulatory databases for the latest company filings.
2. **Extraction**: Dual-library approach (PyMuPDF for text, pdfplumber for tables).
3. **Indexing**: FAISS-based vector storage for RAG (Retrieval-Augmented Generation).
4. **Analysis**: Rule-based agents extract metrics; LLM agents synthesize narrative.
5. **Synthesis**: Map-Reduce summarizing the entire document into an investment view.
6. **Sentiment**: News scraping + Sentiment scoring with time-decay weighting.
7. **Visualization**: Generation of interactive Plotly charts for financial trends.
8. **Interaction**: RAG-enabled chatbot for deep-dive questions with citations.

---

## 🛠️ Tech Stack

- **Backend**: Python 3.10+, Flask
- **PDF Core**: PyMuPDF, pdfplumber
- **Vector DB**: FAISS (Facebook AI Similarity Search)
- **Embeddings**: `bge-small-en-v1.5` (CPU-optimized)
- **LLM API**: Cerebras (Llama 3.3-70b) — *Engine for high-speed synthesis*
- **Frontend**: Vanilla JS, Tailwind CSS, Plotly.js

---

## 🏁 Quick Start

### 1. Prerequisites
- Python 3.10+
- [Cerebras API Key](https://cloud.cerebras.ai/) (Required for LLM analysis)

### 2. Installation
```bash
git clone https://github.com/your-username/XIPO.git
cd XIPO
pip install -r requirements.txt
```

### 3. Configuration
Create a `.env` file in the root directory:
```env
CEREBRAS_API_KEY=your_key_here
PORT=5000
```

### 4. Run the App
```bash
python web_app/app.py
```
Visit `http://localhost:5000` in your browser.

---

## 📂 Project Structure

- `backend/agents/`: Python-based analysis agents (Financial, Risk, Map-Reduce).
- `backend/tools/`: Extraction and scraping utilities.
- `backend/rag/`: FAISS indexing and chatbot logic.
- `web_app/`: Flask server and interactive dashboard.
- `data/`: Analysis results (excluded from Git).

---

## ⚖️ License
MIT License - see [LICENSE](LICENSE) for details.

---
**Built for the next generation of data-driven investors. 🚀**
