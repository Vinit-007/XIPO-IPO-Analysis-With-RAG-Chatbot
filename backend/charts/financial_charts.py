import os
import json
import shutil
import plotly.graph_objects as go
import logging

# Configure logging
logger = logging.getLogger(__name__)

# ===================== HELPERS =====================

def _ensure_dir(path):
    os.makedirs(path, exist_ok=True)

def _save_fig(fig, path):
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(fig.to_json())
        logger.info(f"Saved chart to {path}")
    except Exception as e:
        logger.error(f"Failed to save chart {path}: {str(e)}")

def _load_clean_metrics(company_dir):
    path = os.path.join(company_dir, "extracted", "financial_metrics_clean.json")
    logger.info(f"Loading metrics from: {path}")
    
    if not os.path.exists(path):
        logger.error(f"Clean metrics file NOT FOUND at: {path}")
        return None
        
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            logger.info(f"Loaded JSON keys: {list(data.keys())}")
            if "normalized_metrics_crore" in data:
                logger.info(f"normalized_metrics_crore keys: {list(data['normalized_metrics_crore'].keys())}")
            return data
    except Exception as e:
        logger.error(f"Error reading metrics JSON: {str(e)}")
        return None

def _get_sorted_data(data_dict, metric_name="Unknown"):
    """Sorts dictionary by FY keys and returns (years, values) as plain lists"""
    if not data_dict:
        logger.warning(f"No data dictionary for {metric_name}")
        return [], []
    
    # Sort keys: FY2023 < FY2024
    sorted_keys = sorted(data_dict.keys())
    sorted_vals = [float(data_dict[k]) for k in sorted_keys]  # Ensure float
    
    # DEBUG LOGGING
    logger.info(f"[{metric_name}] X: {sorted_keys}")
    logger.info(f"[{metric_name}] Y: {sorted_vals}")
    
    return sorted_keys, sorted_vals

# ===================== CHARTS =====================

def plot_revenue_trend(metrics, out_dir):
    logger.info("Generating Revenue Trend Chart...")
    data = metrics.get("normalized_metrics_crore", {}).get("revenue", {})
    x, y = _get_sorted_data(data, "Revenue Trend")
    
    if not x: 
        logger.warning("Skipping Revenue Trend - No Data")
        return None

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x, 
        y=y,
        mode='lines+markers',
        line=dict(color='#00F2EA', width=3),
        marker=dict(size=8)
    ))
    
    fig.update_layout(
        title="Revenue Trend (Business Scale)",
        xaxis_title="Fiscal Year",
        yaxis_title="Revenue (₹ Crore)",
        template="plotly_white"
    )
    
    path = os.path.join(out_dir, "1_revenue_trend.json")
    _save_fig(fig, path)
    return path

def plot_pat_trend(metrics, out_dir):
    logger.info("Generating PAT Trend Chart...")
    data = metrics.get("normalized_metrics_crore", {}).get("pat", {})
    x, y = _get_sorted_data(data, "PAT Trend")
    
    if not x: 
        logger.warning("Skipping PAT Trend - No Data")
        return None

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x,
        y=y,
        mode='lines+markers',
        line=dict(color='#8B5CF6', width=3),
        marker=dict(size=8)
    ))
    
    fig.add_hline(y=0, line_dash="dash", line_color="gray")
    
    fig.update_layout(
        title="PAT Trend (Profit/Loss Profile)",
        xaxis_title="Fiscal Year",
        yaxis_title="PAT (₹ Crore)",
        template="plotly_white"
    )

    path = os.path.join(out_dir, "2_pat_trend.json")
    _save_fig(fig, path)
    return path

def plot_eps_trend(metrics, out_dir):
    logger.info("Generating EPS Trend Chart...")
    data = metrics.get("normalized_metrics_crore", {}).get("eps", {})
    x, y = _get_sorted_data(data, "EPS Trend")
    
    if not x: 
        logger.warning("Skipping EPS Trend - No Data")
        return None

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x,
        y=y,
        mode='lines+markers',
        line=dict(color='#F59E0B', width=3),
        marker=dict(size=8)
    ))
    
    fig.update_layout(
        title="EPS Trend (Shareholder Impact)",
        xaxis_title="Fiscal Year",
        yaxis_title="EPS (₹)",
        template="plotly_white"
    )

    path = os.path.join(out_dir, "3_eps_trend.json")
    _save_fig(fig, path)
    return path

def plot_revenue_growth(metrics, out_dir):
    logger.info("Generating Revenue Growth Chart...")
    data = metrics.get("computed_metrics", {}).get("revenue_growth_pct", {})
    x, y = _get_sorted_data(data, "Revenue Growth")
    
    if not x: 
        logger.warning("Skipping Revenue Growth - No Data")
        return None

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=x,
        y=y,
        marker_color='#3B82F6',
        text=[f"{val:.2f}%" for val in y],
        textposition='outside'
    ))
    
    fig.update_layout(
        title="Revenue Growth Momentum",
        xaxis_title="Fiscal Year",
        yaxis_title="Growth (%)",
        template="plotly_white"
    )

    path = os.path.join(out_dir, "4_revenue_growth.json")
    _save_fig(fig, path)
    return path

def plot_profit_margin(metrics, out_dir):
    logger.info("Generating Profit Margin Chart...")
    data = metrics.get("computed_metrics", {}).get("profit_margin_pct", {})
    x, y = _get_sorted_data(data, "Profit Margin")
    
    if not x: 
        logger.warning("Skipping Profit Margin - No Data")
        return None

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x,
        y=y,
        mode='lines+markers',
        line=dict(color='#EC4899', width=3),
        marker=dict(size=8)
    ))
    
    fig.add_hline(y=0, line_dash="dash", line_color="gray")
    
    fig.update_layout(
        title="Profit Margin Trend (Efficiency)",
        xaxis_title="Fiscal Year",
        yaxis_title="Margin (%)",
        template="plotly_white"
    )

    path = os.path.join(out_dir, "5_profit_margin.json")
    _save_fig(fig, path)
    return path

def plot_revenue_vs_pat(metrics, out_dir):
    logger.info("Generating Revenue vs PAT Chart...")
    rev_data = metrics.get("normalized_metrics_crore", {}).get("revenue", {})
    pat_data = metrics.get("normalized_metrics_crore", {}).get("pat", {})
    
    # Get common years
    common_years = sorted(list(set(rev_data.keys()) | set(pat_data.keys())))
    
    if not common_years: 
        logger.warning("Skipping Revenue vs PAT - No Common Data")
        return None
    
    rev_vals = [float(rev_data.get(y, 0)) for y in common_years]
    pat_vals = [float(pat_data.get(y, 0)) for y in common_years]

    # LOGGING
    logger.info(f"[Revenue vs PAT] Years: {common_years}")
    logger.info(f"[Revenue vs PAT] Revenue: {rev_vals}")
    logger.info(f"[Revenue vs PAT] PAT: {pat_vals}")

    fig = go.Figure()

    # Bar for Revenue
    fig.add_trace(go.Bar(
        x=common_years, 
        y=rev_vals, 
        name="Revenue",
        marker_color='#00F2EA',
        yaxis='y'
    ))

    # Line for PAT
    fig.add_trace(go.Scatter(
        x=common_years, 
        y=pat_vals, 
        name="PAT",
        mode="lines+markers",
        line=dict(color='#EF4444', width=3),
        marker=dict(size=8),
        yaxis="y2"
    ))

    fig.update_layout(
        title="Revenue vs PAT (Scale vs Loss)",
        xaxis_title="Fiscal Year",
        yaxis=dict(title="Revenue (₹ Crore)"),
        yaxis2=dict(
            title="PAT (₹ Crore)",
            overlaying="y",
            side="right"
        ),
        legend=dict(x=0, y=1.2, orientation="h"),
        template="plotly_white"
    )

    path = os.path.join(out_dir, "6_revenue_vs_pat.json")
    _save_fig(fig, path)
    return path

# ===================== MASTER =====================

def generate_all_charts(company_dir):
    """
    Generates exactly 6 strict financial charts from clean metrics.
    Clears existing charts first.
    """
    logger.info(f"Starting chart generation for: {company_dir}")
    charts_dir = os.path.join(company_dir, "charts")
    
    # CLEAR EXISTING CHARTS
    if os.path.exists(charts_dir):
        logger.info(f"Clearing existing charts in: {charts_dir}")
        shutil.rmtree(charts_dir)
    _ensure_dir(charts_dir)

    metrics = _load_clean_metrics(company_dir)
    if not metrics:
        return {}

    summary = {
        "revenue_trend": plot_revenue_trend(metrics, charts_dir),
        "pat_trend": plot_pat_trend(metrics, charts_dir),
        "eps_trend": plot_eps_trend(metrics, charts_dir),
        "revenue_growth": plot_revenue_growth(metrics, charts_dir),
        "profit_margin": plot_profit_margin(metrics, charts_dir),
        "revenue_vs_pat": plot_revenue_vs_pat(metrics, charts_dir)
    }

    # Filter None values (missing data)
    summary = {k: v for k, v in summary.items() if v}
    logger.info(f"Generated {len(summary)} charts")

    with open(os.path.join(charts_dir, "charts_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    return summary
