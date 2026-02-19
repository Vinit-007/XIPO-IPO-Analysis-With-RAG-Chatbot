"""
Flask Web Application for IPO Analysis Platform.

Integrates the complete pipeline:
1. PDF download from SEBI
2. Extraction to JSON
3. RAG indexing
4. Structured analysis
5. Charts & visualizations
6. News & sentiment
7. RAG chatbot
"""

import os
import sys
import json
import time
import shutil
import threading
import queue
import logging
from flask import Flask, render_template, request, jsonify, Response, send_from_directory
from flask_cors import CORS

# Add backend to sys path to import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

# Tool imports
from tools.sebi_scraper import fetch_company_rhp
from tools.rhp_extractor import extract_rhp_to_json
from tools.token_utils import prepare_safe_data

# Agent imports
from agents.financial_agent import extract_financial_metrics
from agents.risk_agent import extract_risks
from agents.map_agent import run_map_stage
from agents.reduce_agent import run_reduce_stage
from agents.disclosure_agent import run_disclosure_check

# Chart imports
from charts.financial_charts import generate_all_charts

# Financial Metrics Normalization
from financial_metrics.run_metrics import process_financial_metrics

# News imports
from news.news_scraper import scrape_ipo_news
from news.sentiment_scoring import score_news_articles
from agents.news_agent import analyze_news_impact

# RAG imports (unified system)
# Delayed/Lazy imports for heavy modules to save RAM on startup
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend', 'rag')))
# from rag.rag_orchestrator import copy_extracted_json, ensure_indexed, get_json_path
# from rag.analysis_generator import generate_structured_analysis, save_analysis
# from rag.rag_chatbot_v2 import chat as rag_chat_v2, is_question_blocked, get_blocked_response


# Setup Flask
app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# Global Store (In-memory for demo purposes)
# In production, use Redis/Database
TASKS = {}
LOG_QUEUES = {}


def stream_logs(task_id):
    """Generator to yield logs from the queue for SSE"""
    q = LOG_QUEUES.get(task_id)
    if not q:
        return
    
    while True:
        try:
            # Block for 1 second to wait for new log
            message = q.get(timeout=1.0)
            if message == "AD_FIN":
                yield f"data: PIPELINE_COMPLETED\n\n"
                break
            yield f"data: {message}\n\n"
        except queue.Empty:
            # Send keep-alive
            yield f": keep-alive\n\n"
            continue


def run_pipeline_background(task_id, company_name):
    """
    Executes the IPO Pipeline and streams updates to the queue.
    
    Stages:
    1-2. Fetch RHP from SEBI
    3. Extract PDF to JSON
    4. RAG Indexing (NEW)
    5. Financial & Risk Analysis
    6. Investment Memo Generation
    7. Charts
    8. News
    9. Sentiment
    10. Structured Analysis (NEW)
    11. Enable Chatbot
    """
    log_q = LOG_QUEUES[task_id]
    
    def log(msg):
        print(f"[{task_id}] {msg}")
        log_q.put(msg)
        time.sleep(0.1)  # Small delay for visual effect

    try:
        log(f"🚀 Starting analysis for: {company_name}")
        
        # Setup Directories (Moved up for caching check)
        safe_name = company_name.lower().replace(" ", "_").replace("-", "_")
        BASE_DIR = os.path.join("data", safe_name)
        EXTRACTED_DIR = os.path.join(BASE_DIR, "extracted")
        os.makedirs(EXTRACTED_DIR, exist_ok=True)
        
        STRUCTURED_JSON = os.path.join(EXTRACTED_DIR, "structured.json")
        FIN_JSON = os.path.join(EXTRACTED_DIR, "financial_metrics.json")
        RISK_JSON = os.path.join(EXTRACTED_DIR, "risk_analysis.json")
        REPORT_TXT = os.path.join(EXTRACTED_DIR, "ipo_report.txt")
        NEWS_JSON = os.path.join(EXTRACTED_DIR, "news.json")
        ANALYSIS_JSON = os.path.join(EXTRACTED_DIR, "structured_analysis.json")

        # Check for existing data (Caching)
        if os.path.exists(STRUCTURED_JSON) and os.path.getsize(STRUCTURED_JSON) > 1024:
            log(f"♻️ Found existing data for {company_name}, skipping download & extraction.")
            log(f"📂 Loading from: {STRUCTURED_JSON}")
            
            with open(STRUCTURED_JSON, "r", encoding="utf-8") as f:
                structured_data = json.load(f)
            log(f"✅ Loaded {len(structured_data.get('pages', []))} pages from cache")
            
        else:
            log(f"🔍 Searching SEBI for RHP...")
            
            # STAGE 1 & 2: Fetch RHP
            pdf_paths = fetch_company_rhp(company_name)
            if not pdf_paths:
                log(f"❌ No RHP found for {company_name}")
                log("AD_FIN")
                return

            pdf_path = pdf_paths[0]
            log(f"✅ Found: {os.path.basename(pdf_path)}")
            
            # STAGE 3: Extract PDF to JSON
            log("🧪 STAGE 3: Extracting Text & Tables from PDF...")
            extract_rhp_to_json(pdf_path, STRUCTURED_JSON)
            
            with open(STRUCTURED_JSON, "r", encoding="utf-8") as f:
                structured_data = json.load(f)
            log(f"✅ Extraction Complete: {len(structured_data.get('pages', []))} pages processed")
        
        # STAGE 3.5: Disclosure Update (Addendum/Corrigendum)
        log("🔍 STAGE 3.5: Checking for Addendums/Corrigendums...")
        try:
            update_result = run_disclosure_check(company_name, BASE_DIR)
            if update_result['status'] == 'completed':
                log(f"⚠️ Found and merged {update_result['updates_processed']} updates!")
                # Reload data as it might have changed
                with open(STRUCTURED_JSON, "r", encoding="utf-8") as f:
                    structured_data = json.load(f)
            elif update_result['status'] == 'no_update_found':
                log("✅ No regulatory updates found.")
            else:
                log(f"ℹ️ Disclosure check: {update_result['status']}")
                
        except Exception as e:
            log(f"⚠️ Disclosure Check Warning: {str(e)}")
        
        # STAGE 4: RAG Indexing (NEW)
        log("🔍 STAGE 4: Building RAG Index...")
        try:
            from rag.rag_orchestrator import copy_extracted_json, ensure_indexed
            # Copy to RAG data directory
            rag_json_path = copy_extracted_json(STRUCTURED_JSON, company_name)
            
            # Ensure indexed (will skip if already indexed with same hash)
            index_path = ensure_indexed(rag_json_path)
            log(f"✅ RAG Index Ready: {os.path.basename(index_path)}")
            
            # Store for chat endpoint
            TASKS[task_id]['rag_json_path'] = rag_json_path
        except Exception as e:
            log(f"⚠️ RAG Indexing Warning: {str(e)}")
            TASKS[task_id]['rag_json_path'] = None
        
        # STAGE 5: Financial & Risk Analysis
        log("📊 STAGE 5: Analyzing Financials & Risks...")
        financial_output = extract_financial_metrics(structured_data)
        risk_output = extract_risks(structured_data)
        
        with open(FIN_JSON, "w", encoding="utf-8") as f:
            json.dump(financial_output, f, indent=2)
        with open(RISK_JSON, "w", encoding="utf-8") as f:
            json.dump(risk_output, f, indent=2)
            
        log(f"   💰 Metrics found: {financial_output.get('metrics_found', 0)}")
        log(f"   ⚠️ Risks identified: {len(risk_output.get('risks', []))}")
        
        # STAGE 6: Structured Analysis & Sector Extraction (MOVED UP)
        log("📝 STAGE 6: Generating Structured Analysis & Extracting Sector...")
        extracted_sector = "General"
        try:
            from rag.analysis_generator import generate_structured_analysis, save_analysis
            if TASKS[task_id].get('rag_json_path'):
                analysis = generate_structured_analysis(TASKS[task_id]['rag_json_path'])
                save_analysis(analysis, ANALYSIS_JSON)
                TASKS[task_id]['analysis'] = analysis
                
                # Extract sector for News/ML/Report
                if "sections" in analysis and "ipo_overview" in analysis["sections"]:
                    content = analysis["sections"]["ipo_overview"].get("content", "")
                    match = re.search(r'(?:Sector|Industry|Business Model)\s*(?:/|\\)?\s*(?:Industry)?\s*:?\s*([^\n\r]+)', content, re.IGNORECASE)
                    if match:
                        extracted_sector = match.group(1).strip().strip(".*`")
                        log(f"🏢 Dynamic Sector Identified: {extracted_sector}")
            else:
                log("⚠️ Analysis Skipped (RAG not available)")
        except Exception as e:
            log(f"⚠️ Analysis/Sector Extraction Warning: {str(e)}")

        # STAGE 7: Investment Memo (Map-Reduce)
        log("🧠 STAGE 7: Generating Investment Memo (Map-Reduce)...")
        
        semantic_chunks = [
            {
                "section": "IPO Overview & Verdict",
                "prompt_template": f"Extract COMPANY OVERVIEW for {company_name}.\n" + 
                                   f"Use Sector: {extracted_sector}.\n" +
                                   "Include: Company Name, Sector, legal entity details, and a breakdown of 'Fresh Issue' vs 'Offer for Sale' in millions/crores.\n" +
                                   "DATA:\n{data}",
                "data": prepare_safe_data(structured_data.get("pages", [])[:5])
            },
            {
                "section": "Financial Snapshot",
                "prompt_template": "Extract FINANCIAL SNAPSHOT (Revenue, PAT, Net Worth for last 2-3 years).\nDATA:\n{data}",
                "data": prepare_safe_data(
                    list(financial_output.get("financial_summary", {}).items())[:15]
                )
            }
        ]
        
        partial_reports = run_map_stage(semantic_chunks)
        run_reduce_stage(partial_reports, REPORT_TXT)
        log(f"✅ Report Generated: {REPORT_TXT}")


        # STAGE 8: News (Using Dynamic Sector)
        log(f"📰 STAGE 8: Fetching News for {extracted_sector} sector...")
        news = scrape_ipo_news(company_name, sector=extracted_sector)
        with open(NEWS_JSON, "w", encoding="utf-8") as f:
            json.dump(news, f, indent=2)
        log(f"✅ Found {len(news)} articles")
        
        # STAGE 9: Sentiment
        log("🧠 STAGE 9: Analyzing Market Sentiment...")
        sentiment_result = score_news_articles(news)
        news_sentiment_path = os.path.join(EXTRACTED_DIR, "news_sentiment.json")
        with open(news_sentiment_path, "w", encoding="utf-8") as f:
            json.dump(sentiment_result, f, indent=2)
        log("✅ Sentiment Analysis Complete")

        # STAGE 9.5: Semantic News Analysis (Using Dynamic Sector)
        log("🤖 STAGE 9.5: Running Semantic News Analyst...")
        news_analysis = analyze_news_impact(company_name, extracted_sector, news)
        news_analysis_path = os.path.join(EXTRACTED_DIR, "news_analysis.json")
        with open(news_analysis_path, "w", encoding="utf-8") as f:
            json.dump(news_analysis, f, indent=2)
        log("✅ News Analysis complete")
            
        log(f"✅ Analyst Report: {news_analysis.get('sentiment_label')} Impact")
        
        # Context is now handled by RAG v2 indexing (Stage 4)
        # STAGE 11: Financial Metrics Normalization
        log("📊 STAGE 11: Normalizing Financial Metrics...")
        try:
            import glob
            CLEAN_FIN_JSON = os.path.join(EXTRACTED_DIR, "financial_metrics_clean.json")
            
            # Priority: financial_metrics.json > *_analysis.json
            if os.path.exists(FIN_JSON):
                input_file = FIN_JSON
            else:
                analysis_files = glob.glob(os.path.join(EXTRACTED_DIR, "*_analysis.json"))
                input_file = analysis_files[0] if analysis_files else None
            
            if input_file:
                metrics_result = process_financial_metrics(input_file, CLEAN_FIN_JSON)
                log(f"✅ Normalized Metrics: {CLEAN_FIN_JSON}")
                
                # STAGE 11.2: Charts (Moved from Stage 7)
                log("📈 STAGE 11.2: Generating Interactive Charts...")
                abs_base_dir = os.path.abspath(BASE_DIR)
                try:
                    from charts.financial_charts import generate_all_charts
                    charts = generate_all_charts(abs_base_dir)
                    log(f"✅ {len(charts)} Charts Generated")
                except Exception as chart_err:
                    log(f"⚠️ Chart Generation Failed: {str(chart_err)}")
            else:
                log("⚠️ Stage 11 Skipped: No metrics input file found")
        except Exception as e:
            log(f"⚠️ Metrics Normalization Warning: {str(e)}")

        
        # Context is now handled by RAG v2 indexing (Stage 4)
        log("✅ All stages complete - RAG chatbot ready")
        
        # Update task status
        TASKS[task_id]['status'] = 'COMPLETED'
        TASKS[task_id]['slug'] = safe_name
        
        log("🎉 PIPELINE COMPLETED SUCCESSFULLY")
        log("AD_FIN")
        
    except Exception as e:
        log(f"❌ ERROR: {str(e)}")
        import traceback
        log(traceback.format_exc())
        log("AD_FIN")


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')


@app.route('/api/analyze', methods=['POST'])
def start_analysis():
    data = request.json
    company_name = data.get('company_name')
    if not company_name:
        return jsonify({"error": "Company name required"}), 400
    
    task_id = f"task_{int(time.time())}"
    LOG_QUEUES[task_id] = queue.Queue()
    TASKS[task_id] = {'status': 'RUNNING', 'start_time': time.time()}
    
    # Start Thread
    t = threading.Thread(target=run_pipeline_background, args=(task_id, company_name))
    t.start()
    
    return jsonify({"task_id": task_id, "status": "started"})


@app.route('/api/stream/<task_id>')
def stream(task_id):
    return Response(stream_logs(task_id), mimetype='text/event-stream')


@app.route('/api/report/<task_id>')
def get_report(task_id):
    slug = TASKS.get(task_id, {}).get('slug')
    if not slug:
        return jsonify({"error": "Task not found or not complete"}), 404
        
    base_dir = os.path.join("data", slug, "extracted")
    
    try:
        with open(os.path.join(base_dir, "ipo_report.txt"), "r", encoding="utf-8") as f:
            report_text = f.read()
        
        # Load Charts
        charts_dir = os.path.join("data", slug, "charts")
        chart_files = []
        if os.path.exists(charts_dir):
            chart_files = [f"/data/{slug}/charts/{f}" for f in os.listdir(charts_dir) if f.endswith('.json')]
        
        # Load Structured Analysis (NEW)
        analysis = TASKS.get(task_id, {}).get('analysis')
        if not analysis:
            analysis_path = os.path.join(base_dir, "structured_analysis.json")
            if os.path.exists(analysis_path):
                with open(analysis_path, "r", encoding="utf-8") as f:
                    analysis = json.load(f)

        return jsonify({
            "report": report_text,
            "charts": chart_files,
            "company": slug,
            "analysis": analysis
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/analysis/<task_id>')
def get_analysis(task_id):
    """Get structured analysis for a task."""
    slug = TASKS.get(task_id, {}).get('slug')
    if not slug:
        return jsonify({"error": "Task not found or not complete"}), 404
    
    # Try from memory first
    analysis = TASKS.get(task_id, {}).get('analysis')
    
    # Try from file
    if not analysis:
        analysis_path = os.path.join("data", slug, "extracted", "structured_analysis.json")
        if os.path.exists(analysis_path):
            with open(analysis_path, "r", encoding="utf-8") as f:
                analysis = json.load(f)
    
    if not analysis:
        return jsonify({"error": "Analysis not available"}), 404
    
    return jsonify(analysis)


@app.route('/api/news_analysis/<task_id>')
def get_news_analysis(task_id):
    """Get semantic news analysis for a task."""
    slug = TASKS.get(task_id, {}).get('slug')
    if not slug:
        return jsonify({"error": "Task not found"}), 404
    
    path = os.path.join("data", slug, "extracted", "news_analysis.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return jsonify(json.load(f))
            
    return jsonify({"error": "Analysis not ready"}), 404


@app.route('/api/chat', methods=['POST'])
def chat():
    """
    RAG Chat endpoint.
    
    Uses file-based RAG if available, falls back to context-bundle approach.
    """
    data = request.json
    question = data.get('question')
    task_id = data.get('task_id')
    
    if not question:
        return jsonify({"answer": "Please ask a question."})
    
    # Check for blocked questions
    from rag.rag_chatbot_v2 import is_question_blocked, get_blocked_response
    if is_question_blocked(question):
        return jsonify({"answer": get_blocked_response(), "blocked": True})
    
    # Get task info
    task = TASKS.get(task_id, {})
    slug = task.get('slug')
    rag_json_path = task.get('rag_json_path')
    
    # Use RAG v2 system
    if rag_json_path and os.path.exists(rag_json_path):
        try:
            from rag.rag_chatbot_v2 import chat as rag_chat_v2
            response = rag_chat_v2(rag_json_path, question)
            return jsonify({
                "answer": response.get("answer", "No answer generated."),
                "sources": response.get("sources", []),
                "method": "rag_v2"
            })
        except Exception as e:
            print(f"RAG error: {e}")
            return jsonify({
                "answer": f"Error processing your question: {str(e)}",
                "sources": [],
                "method": "error"
            })
    
    return jsonify({
        "answer": "I'm sorry, but I couldn't find any context to answer your question. Please ensure the analysis pipeline has completed.",
        "sources": [],
        "method": "none"
    })



@app.route('/data/<path:filename>')
def serve_data(filename):
    """Serve generated chart JSONs and images"""
    response = send_from_directory('../data', filename)
    # Prevent browser caching of chart JSONs
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


if __name__ == '__main__':
    app.run(debug=True, port=5000)
