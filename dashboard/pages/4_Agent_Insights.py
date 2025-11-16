"""
Agent Insights - Analytics Dashboard
=====================================
Visualize agent performance, patterns, and learning progress.
"""

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import sys
from pathlib import Path

# Add dashboard directory to path for imports
dashboard_dir = Path(__file__).parent.parent
sys.path.insert(0, str(dashboard_dir))

from components.chat_assistant import render_chat_panel
from components.auth_utils import require_auth

st.set_page_config(
    page_title="Agent Insights",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"  # Show chat for insights
)

# ============================================================================
# AUTHENTICATION CHECK
# ============================================================================
require_auth()
# ============================================================================

# Enhanced CSS for charts and metrics
st.markdown("""
<style>
    .main {
        padding: 1rem 2rem 2rem 2rem;
        max-width: 1400px;
        margin: 0 auto;
    }
    
    h1 {
        font-size: 3.5rem !important;
        font-weight: 800 !important;
        color: #1e3a8a !important;
        text-align: center;
        margin-bottom: 1rem !important;
    }
    
    h2 {
        font-size: 2.25rem !important;
        font-weight: 700 !important;
        color: #1e3a8a !important;
        margin-top: 2.5rem !important;
        margin-bottom: 1.5rem !important;
        border-left: 6px solid #3b82f6;
        padding-left: 1.5rem;
    }
    
    h3 {
        font-size: 1.75rem !important;
        font-weight: 700 !important;
        color: #3b82f6 !important;
        margin-top: 1.5rem !important;
        margin-bottom: 1rem !important;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        padding: 2rem;
        border-radius: 15px;
        border: 3px solid #cbd5e1;
        margin: 1rem 0;
        box-shadow: 0 4px 8px rgba(0,0,0,0.05);
    }
    
    .stMetric {
        background-color: #ffffff !important;
        padding: 1.5rem !important;
        border-radius: 12px !important;
        border: 2px solid #e2e8f0 !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05) !important;
    }
    
    .stMetric label {
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        color: #475569 !important;
    }
    
    .stMetric [data-testid="stMetricValue"] {
        font-size: 2.25rem !important;
        font-weight: 800 !important;
        color: #1e3a8a !important;
    }
    
    /* Chart containers */
    .plot-container {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        border: 2px solid #e2e8f0;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
</style>
""", unsafe_allow_html=True)

# API Configuration
import os

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# Header
st.title("📊 Agent Insights Dashboard")
st.markdown("""
<p style='font-size: 1.5rem; text-align: center; color: #475569; margin-bottom: 2.5rem; font-weight: 500;'>
Analyze agent performance, patterns, and learning progress over time
</p>
""", unsafe_allow_html=True)

# Check API connection
try:
    health_check = requests.get(f"{API_BASE_URL}/health", timeout=5)
    if health_check.status_code != 200:
        st.error("⚠️ Backend API is not responding. Please ensure the backend is running.")
        st.stop()
except:
    st.error("❌ Cannot connect to backend API. Please start the backend with `python3 main.py`")
    st.stop()

# Fetch data from API
@st.cache_data(ttl=60)  # Cache for 60 seconds
def fetch_audit_data():
    """Fetch audit trail data"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/audit/entries?limit=1000", timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get("entries", [])
        return []
    except Exception as e:
        st.error(f"Error fetching audit data: {e}")
        return []

@st.cache_data(ttl=60)
def fetch_feedback_data():
    """Fetch human feedback data"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/feedback?limit=1000", timeout=10)
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        st.error(f"Error fetching feedback data: {e}")
        return []

@st.cache_data(ttl=60)
def fetch_feedback_stats():
    """Fetch feedback statistics"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/feedback/stats", timeout=10)
        if response.status_code == 200:
            return response.json()
        return {}
    except Exception as e:
        st.error(f"Error fetching feedback stats: {e}")
        return {}

def flatten_audit_entry(entry):
    """Flatten nested API response into flat dictionary"""
    # Check for None entry
    if entry is None:
        return None
    
    try:
        return {
            'audit_id': entry.get('audit_id'),
            'timestamp': entry.get('timestamp'),
            'agent_type': entry.get('agent_type'),
            # Task fields
            'task_description': entry.get('task', {}).get('description', ''),
            'task_category': entry.get('task', {}).get('category', ''),
            # Entity fields
            'entity_name': entry.get('entity', {}).get('name', ''),
            'entity_type': entry.get('entity', {}).get('type', ''),
            # Decision fields (CRITICAL: these are nested!)
            'decision_outcome': entry.get('decision', {}).get('outcome', ''),
            'decision_confidence': entry.get('decision', {}).get('confidence_score', 0),
            'risk_level': entry.get('decision', {}).get('risk_level', ''),
            'risk_score': entry.get('decision', {}).get('risk_score', 0),
            # Entity context (for jurisdictions)
            'jurisdictions': entry.get('entity_context', {}).get('jurisdictions', []),
            'industry': entry.get('entity_context', {}).get('industry', ''),
            # Risk factors (keep as dict for detailed analysis)
            'risk_factors': entry.get('risk_factors', {}),
            # Reasoning chain
            'reasoning_chain': entry.get('reasoning_chain', []),
            'escalation_reason': entry.get('escalation_reason', ''),
        }
    except Exception as e:
        # Silently skip malformed entries
        return None

# Load data
with st.spinner("Loading agent data..."):
    audit_entries = fetch_audit_data()
    feedback_entries = fetch_feedback_data()
    feedback_stats = fetch_feedback_stats()

if not audit_entries:
    st.info("""
    📊 **No Data Available Yet**
    
    The agent hasn't made any decisions yet. Start using the system to see insights:
    - Go to "Check a Task" to analyze your first task
    - Return here to see beautiful charts and analytics
    
    Charts will appear automatically as you use the system!
    """)
    st.stop()

# Convert to DataFrame with flattened structure
# Filter out None entries first, then filter out None results from flattening
flattened_entries = [flatten_audit_entry(entry) for entry in audit_entries if entry is not None]
flattened_entries = [entry for entry in flattened_entries if entry is not None]
df_audit = pd.DataFrame(flattened_entries)

# Convert timestamp to datetime
df_audit['timestamp'] = pd.to_datetime(df_audit['timestamp'])
df_audit['date'] = df_audit['timestamp'].dt.date

# Summary Metrics
st.markdown("## 📈 Key Metrics")

col1, col2, col3, col4 = st.columns(4)

with col1:
    total_decisions = len(df_audit)
    st.metric("Total Decisions", f"{total_decisions:,}", help="Total number of decisions made by the agent")

with col2:
    avg_confidence = df_audit['decision_confidence'].mean() * 100 if 'decision_confidence' in df_audit.columns else 0
    st.metric("Avg Confidence", f"{avg_confidence:.1f}%", help="Average confidence across all decisions")

with col3:
    escalation_rate = (df_audit['decision_outcome'] == 'ESCALATE').sum() / total_decisions * 100 if total_decisions > 0 else 0
    st.metric(
        "Escalation Rate ℹ️", 
        f"{escalation_rate:.1f}%", 
        help="Percentage of tasks that required escalation to human experts. Lower rates indicate better AI autonomy."
    )

with col4:
    if feedback_stats and feedback_stats.get('total_feedback_count', 0) > 0:
        ai_accuracy = feedback_stats.get('accuracy_percent', 0)
        st.metric(
            "AI Accuracy ℹ️", 
            f"{ai_accuracy:.1f}%", 
            help="Percentage of AI decisions confirmed correct by humans. Calculated as: (agreements / total feedback) × 100. Higher accuracy indicates more trustworthy AI."
        )
    else:
        st.metric("AI Accuracy ℹ️", "N/A", help="No feedback data available yet. Submit feedback on decisions to see accuracy metrics.")

st.markdown("---")

# 1. Confidence Score Trend (Line Chart)
st.markdown("## 📊 Confidence Score Trend")
st.markdown("Track how confident the agent is over time. Higher confidence indicates clearer scenarios.")

# Group by date and calculate average confidence
confidence_by_date = df_audit.groupby('date')['decision_confidence'].agg(['mean', 'count']).reset_index()
confidence_by_date['mean'] = confidence_by_date['mean'] * 100

fig_confidence = px.line(
    confidence_by_date, 
    x='date', 
    y='mean',
    title='Average Confidence Score Over Time',
    labels={'mean': 'Confidence (%)', 'date': 'Date'},
    markers=True
)

fig_confidence.update_traces(
    line=dict(color='#3b82f6', width=3),
    marker=dict(size=8, color='#1e40af')
)

fig_confidence.add_hline(
    y=85, 
    line_dash="dash", 
    line_color="green", 
    annotation_text="High Confidence (85%)"
)

fig_confidence.add_hline(
    y=70, 
    line_dash="dash", 
    line_color="orange", 
    annotation_text="Moderate Confidence (70%)"
)

fig_confidence.update_layout(
    height=400,
    hovermode='x unified',
    plot_bgcolor='white',
    paper_bgcolor='white',
    font=dict(size=12)
)

st.plotly_chart(fig_confidence, use_container_width=True)

# Show insight
recent_confidence = confidence_by_date['mean'].iloc[-1] if len(confidence_by_date) > 0 else 0
if recent_confidence >= 85:
    st.success(f"✅ Recent confidence is high ({recent_confidence:.1f}%). The agent is very confident in its decisions.")
elif recent_confidence >= 70:
    st.info(f"💡 Recent confidence is moderate ({recent_confidence:.1f}%). The agent is performing well.")
else:
    st.warning(f"⚠️ Recent confidence is low ({recent_confidence:.1f}%). Consider reviewing decision patterns.")

st.markdown("---")

# 2. Escalations Over Time
st.markdown("## 🚨 Escalations Over Time")
st.markdown("Monitor how often tasks require expert escalation. Trends can indicate organizational compliance maturity.")

# Count decisions by date and type
decisions_by_date = df_audit.groupby(['date', 'decision_outcome']).size().reset_index(name='count')

fig_escalations = px.area(
    decisions_by_date,
    x='date',
    y='count',
    color='decision_outcome',
    title='Decision Types Over Time',
    labels={'count': 'Number of Decisions', 'date': 'Date', 'decision_outcome': 'Decision Type'},
    color_discrete_map={
        'AUTONOMOUS': '#10b981',
        'REVIEW_REQUIRED': '#f59e0b',
        'ESCALATE': '#ef4444'
    }
)

fig_escalations.update_layout(
    height=400,
    hovermode='x unified',
    plot_bgcolor='white',
    paper_bgcolor='white',
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

st.plotly_chart(fig_escalations, use_container_width=True)

# Calculate escalation trend
if len(df_audit) >= 10:
    recent_escalation_rate = (df_audit.tail(10)['decision_outcome'] == 'ESCALATE').sum() / 10 * 100
    early_escalation_rate = (df_audit.head(10)['decision_outcome'] == 'ESCALATE').sum() / 10 * 100
    trend = recent_escalation_rate - early_escalation_rate
    
    if trend < -10:
        st.success(f"📉 Escalation rate is decreasing ({abs(trend):.1f}% reduction). Organization compliance maturity is improving!")
    elif trend > 10:
        st.warning(f"📈 Escalation rate is increasing ({trend:.1f}% increase). Consider reviewing compliance processes.")
    else:
        st.info(f"➡️ Escalation rate is stable (±{abs(trend):.1f}%). Consistent compliance patterns maintained.")

st.markdown("---")

# 3. Top Risk Factors by Frequency
st.markdown("## ⚠️ Top Risk Factors by Frequency")
st.markdown("Identify which risk factors appear most often in high-risk decisions.")

# Extract risk factors from high-risk decisions
high_risk_entries = df_audit[df_audit['risk_level'] == 'HIGH']

if len(high_risk_entries) > 0:
    # Analyze risk factors
    risk_factor_counts = {
        'Jurisdiction Risk': 0,
        'Entity Risk': 0,
        'Task Risk': 0,
        'Data Sensitivity': 0,
        'Regulatory Risk': 0,
        'Impact Risk': 0
    }
    
    for _, row in high_risk_entries.iterrows():
        risk_factors = row.get('risk_factors', {})
        if isinstance(risk_factors, dict):
            if risk_factors.get('jurisdiction_risk', 0) > 0.6:
                risk_factor_counts['Jurisdiction Risk'] += 1
            if risk_factors.get('entity_risk', 0) > 0.6:
                risk_factor_counts['Entity Risk'] += 1
            if risk_factors.get('task_risk', 0) > 0.6:
                risk_factor_counts['Task Risk'] += 1
            if risk_factors.get('data_sensitivity_risk', 0) > 0.6:
                risk_factor_counts['Data Sensitivity'] += 1
            if risk_factors.get('regulatory_risk', 0) > 0.6:
                risk_factor_counts['Regulatory Risk'] += 1
            if risk_factors.get('impact_risk', 0) > 0.6:
                risk_factor_counts['Impact Risk'] += 1
    
    # Create DataFrame for plotting
    df_risk_factors = pd.DataFrame([
        {'Risk Factor': k, 'Frequency': v} 
        for k, v in risk_factor_counts.items()
    ]).sort_values('Frequency', ascending=True)
    
    fig_risk_factors = px.bar(
        df_risk_factors,
        x='Frequency',
        y='Risk Factor',
        orientation='h',
        title='High-Risk Factors (>60% threshold) in High-Risk Decisions',
        labels={'Frequency': 'Number of Occurrences', 'Risk Factor': ''},
        color='Frequency',
        color_continuous_scale='Reds'
    )
    
    fig_risk_factors.update_layout(
        height=400,
        showlegend=False,
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    st.plotly_chart(fig_risk_factors, use_container_width=True)
    
    # Show top risk factor
    top_factor = df_risk_factors.iloc[-1]
    if top_factor['Frequency'] > 0:
        st.info(f"🔍 **Most Common High-Risk Factor**: {top_factor['Risk Factor']} appears in {top_factor['Frequency']} high-risk decisions.")
else:
    st.info("No high-risk decisions recorded yet. This chart will populate as high-risk cases are analyzed.")

st.markdown("---")

# 4. Jurisdiction Heatmap
st.markdown("## 🌍 Jurisdiction Activity Heatmap")
st.markdown("Visualize which jurisdictions are most frequently involved in decisions.")

# Extract jurisdictions from flattened data
jurisdiction_counts = {}

for _, row in df_audit.iterrows():
    jurisdictions = row.get('jurisdictions', [])
    if isinstance(jurisdictions, list):
        for jurisdiction in jurisdictions:
            jurisdiction_counts[jurisdiction] = jurisdiction_counts.get(jurisdiction, 0) + 1

if jurisdiction_counts:
    # Create DataFrame
    df_jurisdictions = pd.DataFrame([
        {'Jurisdiction': k, 'Count': v}
        for k, v in jurisdiction_counts.items()
    ]).sort_values('Count', ascending=False)
    
    # Jurisdiction name mapping
    jurisdiction_names = {
        'US_FEDERAL': 'United States (Federal)',
        'US_CA': 'California',
        'US_NY': 'New York',
        'EU': 'European Union',
        'UK': 'United Kingdom',
        'CANADA': 'Canada',
        'AUSTRALIA': 'Australia',
        'MULTI_JURISDICTIONAL': 'Multi-Jurisdictional'
    }
    
    df_jurisdictions['Name'] = df_jurisdictions['Jurisdiction'].map(
        lambda x: jurisdiction_names.get(x, x)
    )
    
    fig_jurisdictions = px.treemap(
        df_jurisdictions,
        path=['Name'],
        values='Count',
        title='Jurisdiction Distribution (Treemap)',
        color='Count',
        color_continuous_scale='Blues',
        hover_data={'Count': True}
    )
    
    fig_jurisdictions.update_layout(
        height=500,
        paper_bgcolor='white'
    )
    
    st.plotly_chart(fig_jurisdictions, use_container_width=True)
    
    # Show top jurisdictions
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### Top 3 Jurisdictions")
        for i, row in df_jurisdictions.head(3).iterrows():
            st.metric(row['Name'], row['Count'], help=f"Number of decisions involving {row['Name']}")
    
    with col2:
        # Calculate multi-jurisdictional complexity
        multi_jurisdiction_decisions = sum(1 for _, row in df_audit.iterrows() 
                                          if isinstance(row.get('jurisdictions', []), list) 
                                          and len(row.get('jurisdictions', [])) > 1)
        
        if multi_jurisdiction_decisions > 0:
            multi_pct = (multi_jurisdiction_decisions / len(df_audit)) * 100
            st.metric("Multi-Jurisdictional", f"{multi_pct:.1f}%", 
                     help="Percentage of decisions involving multiple jurisdictions")
else:
    st.info("No jurisdiction data available yet.")

st.markdown("---")

# 5. AI vs Human Override Rates
st.markdown("## 🤖 vs 👤 AI vs Human Agreement")
st.markdown("Compare AI decisions with human feedback to track learning accuracy.")

if feedback_stats and feedback_stats.get('total_feedback_count', 0) > 0:
    # Create visualization for override rates
    col1, col2 = st.columns(2)
    
    with col1:
        # Pie chart of agreement vs override
        fig_agreement = go.Figure(data=[go.Pie(
            labels=['AI Correct', 'Human Override'],
            values=[
                feedback_stats.get('agreement_count', 0),
                feedback_stats.get('override_count', 0)
            ],
            marker=dict(colors=['#10b981', '#ef4444']),
            hole=0.4
        )])
        
        fig_agreement.update_layout(
            title='AI Accuracy: Agreement vs Override',
            height=400,
            showlegend=True,
            paper_bgcolor='white'
        )
        
        st.plotly_chart(fig_agreement, use_container_width=True)
    
    with col2:
        # Bar chart of override breakdown by decision type
        override_breakdown = feedback_stats.get('override_breakdown', {})
        
        if override_breakdown:
            df_overrides = pd.DataFrame([
                {'Decision Type': k, 'Overrides': v}
                for k, v in override_breakdown.items()
            ]).sort_values('Overrides', ascending=False)
            
            fig_overrides = px.bar(
                df_overrides,
                x='Decision Type',
                y='Overrides',
                title='Override Count by Decision Type',
                labels={'Overrides': 'Number of Overrides'},
                color='Overrides',
                color_continuous_scale='Reds'
            )
            
            fig_overrides.update_layout(
                height=400,
                showlegend=False,
                plot_bgcolor='white',
                paper_bgcolor='white'
            )
            
            st.plotly_chart(fig_overrides, use_container_width=True)
    
    # Summary metrics
    st.markdown("### Learning Progress")
    
    accuracy = feedback_stats.get('accuracy_percent', 0)
    total_feedback = feedback_stats.get('total_feedback_count', 0)
    most_overridden = feedback_stats.get('most_overridden_decision')
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Overall Accuracy", f"{accuracy:.1f}%", 
                 help="Percentage of AI decisions confirmed correct by humans")
    
    with col2:
        st.metric("Total Feedback", total_feedback,
                 help="Number of human feedback entries collected")
    
    with col3:
        if most_overridden:
            st.metric("Most Overridden", most_overridden,
                     help="Decision type that humans correct most often")
        else:
            st.metric("Most Overridden", "None",
                     help="No overrides yet - AI is perfect so far!")
    
    # Learning insights
    if accuracy >= 85:
        st.success(f"""
        ✅ **Excellent Performance** ({accuracy:.1f}%)
        
        The AI is making highly accurate decisions. Human feedback confirms the agent 
        is performing exceptionally well. Continue current patterns.
        """)
    elif accuracy >= 70:
        st.info(f"""
        💡 **Good Performance** ({accuracy:.1f}%)
        
        The AI is performing well with room for improvement. Continue collecting feedback 
        to help the agent learn edge cases and improve accuracy.
        """)
    else:
        st.warning(f"""
        ⚠️ **Learning in Progress** ({accuracy:.1f}%)
        
        The AI is still learning. More feedback data will help improve accuracy. 
        This is normal for new deployments - accuracy typically improves over time.
        """)

else:
    st.info("""
    📊 **No Feedback Data Yet**
    
    Human feedback hasn't been collected yet. To see AI vs Human comparison:
    1. Analyze a task on the "Check a Task" page
    2. Submit feedback using the "Human Feedback" section
    3. Return here to see accuracy metrics and override patterns
    
    The learning loop requires human feedback to calculate accuracy!
    """)

st.markdown("---")

# Additional Insights Section
st.markdown("## 🔍 Additional Insights")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### Decision Distribution")
    decision_counts = df_audit['decision_outcome'].value_counts()
    
    fig_decisions = px.pie(
        values=decision_counts.values,
        names=decision_counts.index,
        title='Overall Decision Distribution',
        color=decision_counts.index,
        color_discrete_map={
            'AUTONOMOUS': '#10b981',
            'REVIEW_REQUIRED': '#f59e0b',
            'ESCALATE': '#ef4444'
        }
    )
    
    fig_decisions.update_layout(height=350, paper_bgcolor='white')
    st.plotly_chart(fig_decisions, use_container_width=True)

with col2:
    st.markdown("### Risk Level Distribution")
    risk_counts = df_audit['risk_level'].value_counts()
    
    fig_risks = px.pie(
        values=risk_counts.values,
        names=risk_counts.index,
        title='Overall Risk Level Distribution',
        color=risk_counts.index,
        color_discrete_map={
            'LOW': '#10b981',
            'MEDIUM': '#f59e0b',
            'HIGH': '#ef4444'
        }
    )
    
    fig_risks.update_layout(height=350, paper_bgcolor='white')
    st.plotly_chart(fig_risks, use_container_width=True)

st.markdown("---")

# Data Export
st.markdown("## 💾 Export Data")
st.markdown("Download raw data for further analysis in your preferred tools.")

col1, col2 = st.columns(2)

with col1:
    # Export audit data
    csv_audit = df_audit.to_csv(index=False)
    st.download_button(
        label="📊 Download Audit Data (CSV)",
        data=csv_audit,
        file_name=f"agent_audit_data_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
        use_container_width=True
    )

with col2:
    # Export feedback data
    if feedback_entries:
        df_feedback = pd.DataFrame(feedback_entries)
        csv_feedback = df_feedback.to_csv(index=False)
        st.download_button(
            label="👤 Download Feedback Data (CSV)",
            data=csv_feedback,
            file_name=f"agent_feedback_data_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    else:
        st.info("No feedback data available for export yet")

st.markdown("---")

# Chat Assistant in Sidebar
with st.sidebar:
    st.markdown("---")
    st.markdown("## 💬 AI Chat Assistant")
    st.caption("Ask about analytics & insights")
    
    # Render chat panel
    render_chat_panel(context_data={
        "page": "Agent Insights",
        "entity_name": "Analytics Dashboard",
        "task_description": "Ask questions about agent performance, trends, or specific metrics"
    })

# Footer
st.markdown("""
<div style='text-align: center; color: #64748b; padding: 2rem; font-size: 1rem;'>
    <p style='font-weight: 600;'>📊 Agent Insights Dashboard</p>
    <p>Data refreshes every 60 seconds. Last updated: {}</p>
    <p>For questions about these metrics, refer to the documentation or contact your IT support team.</p>
</div>
""".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')), unsafe_allow_html=True)
