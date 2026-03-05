# 🛡️ CyberPresales AI Assistant

> An AI-powered RFP analyzer and presales automation tool for cybersecurity solution architects.

![Python](https://img.shields.io/badge/Python-3.9+-blue?style=flat-square)
![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-red?style=flat-square)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--3.5-green?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)

---

## 🎯 Problem Statement

As a cybersecurity presales consultant, analyzing RFPs manually takes **3-5 hours per document**. 
This tool reduces that to **under 5 minutes** by automating:
- Requirement extraction
- Domain classification
- Product/vendor mapping
- Executive summary generation
- Interactive Q&A on the document

---

## ✨ Features

| Feature | Description | Time Saved |
|---|---|---|
| 📋 **RFP Summary** | Extracts & structures all key requirements | 2-3 hrs → 2 min |
| 🎯 **Domain Classifier** | Auto-detects SIEM, EDR, ZeroTrust, Cloud, Network, GRC | Manual → Instant |
| 🛒 **Product Mapping** | Maps requirements to vendor solutions (Palo Alto, Microsoft, CrowdStrike, etc.) | 1 hr → 2 min |
| 📝 **Executive Summary** | Board-ready summary for proposals | 1 hr → 1 min |
| 💬 **Chat with RFP** | Ask any question about the document | Search time → Instant |

---

## 🚀 Getting Started

### Prerequisites
- Python 3.9+
- OpenAI API key ([Get one here](https://platform.openai.com))

### Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/cyberpresales-ai.git
cd cyberpresales-ai

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

### Usage
1. Open the app in your browser (http://localhost:8501)
2. Enter your OpenAI API key in the sidebar
3. Upload an RFP (PDF or Word) — or use the sample RFP
4. Click through each tab to get analysis, domain detection, product mapping, and executive summary
5. Use the chat tab to ask specific questions about the RFP

---

## 🏗️ Architecture

```
cyberpresales-ai/
├── app.py                    # Main Streamlit application
├── utils/
│   ├── document_processor.py # PDF/DOCX text extraction
│   └── ai_engine.py          # OpenAI API functions
├── requirements.txt
└── README.md
```

**Tech Stack:**
- **Frontend:** Streamlit
- **AI/LLM:** OpenAI GPT-3.5-turbo
- **Document Processing:** PyPDF, python-docx
- **Language:** Python

---

## 💡 Use Cases

- **Presales Consultants** — Rapid RFP analysis before customer meetings
- **Solution Architects** — Quick requirement mapping to solution components
- **Bid Managers** — Executive summary generation for proposals
- **Sales Teams** — Understanding technical requirements without deep reading

---

## 🗺️ Roadmap

- [ ] LangChain RAG for multi-document analysis
- [ ] Auto-generate full proposal deck
- [ ] Competitive analysis feature
- [ ] Export to PDF/PPT
- [ ] Support for Excel-based RFPs
- [ ] Multi-language RFP support

---

## 👤 Author

**Yash Mehrotra**  
Solution Architect | Cybersecurity Presales | GenAI Enthusiast  
[LinkedIn](https://linkedin.com/in/YOUR_PROFILE) | [GitHub](https://github.com/YOUR_USERNAME)

---

## 📄 License

MIT License — feel free to use and adapt for your own presales workflows.
