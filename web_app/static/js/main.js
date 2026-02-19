const urlParams = new URLSearchParams(window.location.search);
let taskId = urlParams.get('task_id');

const term = document.getElementById('terminal');
const statusBadge = document.getElementById('metrics-status');
const reportContainer = document.getElementById('report-container');
const chatInput = document.getElementById('chat-input');
const sendBtn = document.getElementById('send-btn');
const chartsContainer = document.getElementById('charts-container');

// Auto-start analysis if company name is in sessionStorage
window.addEventListener('DOMContentLoaded', async function () {
    const companyName = sessionStorage.getItem('companyName');

    if (companyName && !taskId) {
        // Clear the stored name
        sessionStorage.removeItem('companyName');

        // Show status
        statusBadge.innerText = `Starting analysis for: ${companyName}`;
        statusBadge.style.color = "#00f2ea";

        // Start the analysis
        try {
            const response = await fetch('/api/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ company_name: companyName })
            });

            const data = await response.json();

            if (data.task_id) {
                taskId = data.task_id;
                // Update URL without reload
                const newUrl = `${window.location.pathname}?task_id=${taskId}`;
                window.history.pushState({ path: newUrl }, '', newUrl);

                // Start listening to the stream
                startStreamListener();
            }
        } catch (error) {
            console.error('Failed to start analysis:', error);
            statusBadge.innerText = 'Error: Failed to start analysis';
            statusBadge.style.color = '#ff0055';
        }
    } else if (taskId) {
        // Existing task, start listener
        startStreamListener();
    }
});

// Chat Functions
async function sendMessage() {
    const text = chatInput.value.trim();
    if (!text) return;

    // UI
    addMessage(text, 'user');
    chatInput.value = '';

    // API
    try {
        const res = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                question: text,
                task_id: taskId
            })
        });
        const data = await res.json();
        addMessage(data.answer || "Sorry, I couldn't get an answer.", 'bot');
    } catch (e) {
        addMessage("Error communicating with bot.", 'bot');
    }
}

function addMessage(text, type) {
    const div = document.createElement('div');
    div.className = `msg ${type}`;
    div.innerText = text;
    document.getElementById('chat-history').appendChild(div);
    document.getElementById('chat-history').scrollTop = 9999;
}

// Stream listener function
function startStreamListener() {
    if (!taskId) return;

    const evtSource = new EventSource(`/api/stream/${taskId}`);

    evtSource.onmessage = function (event) {
        if (event.data === "PIPELINE_COMPLETED") {
            // terminal update skipped
            evtSource.close();
            statusBadge.innerText = "Status: COMPLETE";
            statusBadge.style.color = "#00ff00";
            loadResults();
        } else {
            // Optional: update a small status text somewhere if needed, 
            // but user wants terminal replaced. We just ignore logs visually.
            statusBadge.innerText = "Status: PROCESSING...";
        }
    };

    evtSource.onerror = function () {
        console.log("Stream closed or error.");
        evtSource.close();
    };
}

async function loadResults() {
    try {
        const res = await fetch(`/api/report/${taskId}`);
        const data = await res.json();

        if (data.report) {
            // Render Markdown Report
            reportContainer.innerHTML = marked.parse(data.report);

            // Enable Chat
            chatInput.disabled = false;
            sendBtn.disabled = false;
            addMessage("I have analyzed the report. What would you like to know?", 'bot');

            // Trigger News Articles Load (NEW)
            if (data.company) {
                loadNewsArticles(data.company);
            }

            // Financial Health (NEW)
            if (data.health) {
                const h = data.health;
                const card = document.getElementById('health-card');
                if (card) {
                    card.style.display = 'block';
                    document.getElementById('health-score-val').innerText = h.overall_score || '--';

                    // Update Ranking Text
                    const rankingSpan = document.getElementById('health-ranking-text');
                    if (rankingSpan && h.overall_score) {
                        const topPct = 100 - parseInt(h.overall_score);
                        rankingSpan.innerText = `Top ${topPct}% of Peers`;
                    }

                    const p = h.feature_percentiles || h.percentiles || {};
                    const formatPct = (val) => val ? Math.round(val) + '%' : '--';

                    document.getElementById('health-growth').innerText = formatPct(p.revenue_growth);
                    document.getElementById('health-stability').innerText = formatPct(p.revenue_stability);
                    document.getElementById('health-margins').innerText = formatPct(p.profit_margin);
                    document.getElementById('health-efficiency').innerText = formatPct(p.asset_turnover_latest || p.ebitda_margin_avg); // Fallback
                }
            }
        }

        // Charts Logic
        if (data.charts && data.charts.length > 0) {
            const chartsRow = document.querySelector('.charts-row');
            if (chartsRow) chartsRow.style.display = 'block';

            chartsContainer.innerHTML = '';

            // Loop through chart files
            for (const chartUrl of data.charts) {
                try {
                    const chartRes = await fetch(chartUrl);
                    if (!chartRes.ok) continue;

                    const chartData = await chartRes.json();

                    const wrapper = document.createElement('div');
                    wrapper.className = 'chart-wrapper';
                    wrapper.style.minHeight = '350px';
                    wrapper.id = `chart-${Math.random().toString(36).substr(2, 9)}`;
                    chartsContainer.appendChild(wrapper);

                    // Render Plotly Chart
                    Plotly.newPlot(wrapper.id, chartData.data, chartData.layout, { responsive: true });

                } catch (err) {
                    console.error("Error loading chart:", err);
                }
            }
        }

    } catch (e) {
        console.error("Error loading results:", e);
        reportContainer.innerHTML = `<div style="color:red;">Failed to load report data.</div>`;
    }
}
// toggleLogs removed as UI is now News-only by default

// News Cards & Sentiment Logic
async function loadNewsArticles(slug) {
    const newsContainer = document.getElementById('latest-news-container');
    const narrativeDiv = document.getElementById('news-narrative');
    const driversList = document.getElementById('news-drivers');
    const scoreSpan = document.getElementById('sentiment-score');
    const badge = document.getElementById('sentiment-badge');

    // 1. Load Sentiment Analysis (Structured Narrative)
    try {
        const sentRes = await fetch(`/data/${slug}/extracted/news_analysis.json`);
        if (sentRes.ok) {
            const sentData = await sentRes.json();

            // Update Score & Badge
            const score = sentData.sentiment_score;
            scoreSpan.innerText = score;

            const label = sentData.sentiment_label;
            badge.innerText = label;

            // Color coding
            if (label && (label.includes("POSITIVE") || label.includes("BULLISH"))) {
                badge.style.background = "rgba(74, 222, 128, 0.2)"; // Green
                badge.style.color = "#4ade80";
            } else if (label && (label.includes("NEGATIVE") || label.includes("BEARISH"))) {
                badge.style.background = "rgba(248, 113, 113, 0.2)"; // Red
                badge.style.color = "#f87171";
            } else {
                badge.style.background = "rgba(255, 255, 255, 0.1)"; // Grey
                badge.style.color = "#fff";
            }

            // Narrative
            narrativeDiv.innerText = sentData.narrative || sentData.market_narrative || "Analysis available.";

            // Drivers (Key Factors)
            driversList.innerHTML = '';
            const drivers = sentData.key_factors || sentData.key_drivers || [];
            drivers.forEach(d => {
                const li = document.createElement('li');
                li.innerText = d;
                li.style.marginBottom = '0.5rem';
                driversList.appendChild(li);
            });

        } else {
            narrativeDiv.innerText = "Sentiment analysis not yet generated.";
        }
    } catch (e) {
        console.error("Failed to load sentiment:", e);
    }

    // 2. Load Articles
    try {
        const res = await fetch(`/data/${slug}/extracted/news.json`);
        if (res.ok) {
            const newsItems = await res.json();
            newsContainer.innerHTML = '';

            if (newsItems.length === 0) {
                newsContainer.innerHTML = '<div style="color:#666; font-style:italic;">No articles found.</div>';
                return;
            }

            newsItems.forEach(item => {
                const card = document.createElement('div');
                card.className = 'news-card';

                // Format Date
                let dateStr = item.published_at || item.scraped_at || 'Recent';

                // Truncate headline
                const headline = item.headline.length > 80 ? item.headline.substring(0, 80) + '...' : item.headline;

                card.innerHTML = `
                    <h5>${headline}</h5>
                    <div class="news-meta">
                        <span class="news-source-badge">${item.source || 'News'}</span>
                        <span>${dateStr}</span>
                    </div>
                    <div style="margin-top:0.5rem; display:flex; justify-content:flex-end;">
                        <a href="${item.url}" target="_blank" class="read-more-link">Read more →</a>
                    </div>
                `;
                newsContainer.appendChild(card);
            });
        }
    } catch (e) {
        console.error("Failed to load news articles:", e);
        newsContainer.innerHTML = '<div style="color:#666;">Unable to load news feed.</div>';
    }
}



// Auto-load results if task_id is present (Handles Refresh/Direct Link)
if (taskId) {
    loadResults();
}
