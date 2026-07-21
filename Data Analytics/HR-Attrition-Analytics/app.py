import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os

# ==========================================
# 1. PAGE CONFIGURATION & CUSTOM CSS
# ==========================================
st.set_page_config(page_title="HR Attrition Analytics", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    :root {
        --bg-color: #0f172a;
        --card-bg: #1e293b;
        --text-main: #f8fafc;
        --text-muted: #94a3b8;
        --primary: #3b82f6;
        --accent-teal: #14b8a6;
        --danger: #ef4444;
        --warning: #f59e0b;
        --success: #10b981;
    }
    
    /* Main App Background */
    .stApp {
        background-color: var(--bg-color);
        color: var(--text-main);
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #111827;
        border-right: 1px solid #334155;
    }
    section[data-testid="stSidebar"] .stMarkdown, section[data-testid="stSidebar"] label {
        color: var(--text-main) !important;
    }
    
    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #1e293b;
        border-radius: 12px;
        padding: 8px;
        border: 1px solid #334155;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 24px;
        border-radius: 8px;
        color: var(--text-muted);
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background-color: var(--primary);
        color: white !important;
    }
    
    /* Metric Cards */
    div[data-testid="stMetric"] {
        background-color: var(--card-bg);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 16px;
        border-left: 4px solid var(--primary);
    }
    div[data-testid="stMetric"] label {
        color: var(--text-muted);
        font-size: 0.85rem !important;
        font-weight: 600;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: var(--text-main);
        font-size: 1.8rem !important;
        font-weight: 800;
    }
    
    /* Custom Containers for Charts */
    .stPlotlyChart {
        background-color: var(--card-bg) !important;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 10px;
    }
    
    /* Headers */
    h1, h2, h3, h4 {
        color: var(--text-main) !important;
    }
    
    /* Actionable insight boxes */
    .insight-box {
        background-color: #1e293b;
        border-left: 4px solid var(--accent-teal);
        padding: 16px;
        border-radius: 8px;
        color: var(--text-main);
        margin-bottom: 10px;
    }
    .insight-box h4 {
        margin-top: 0;
        color: var(--accent-teal);
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATA LOADING (DYNAMIC CSV + FALLBACK)
# ==========================================
@st.cache_data
def load_data():
    csv_path = "WA_Fn-UseC_-HR-Employee-Attrition.csv"
    
    # Check if the real CSV exists in the directory
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
    else:
        # Fallback: Generate mock data with the EXACT same schema if CSV is missing
        # This ensures the app runs out-of-the-box for testing
        np.random.seed(42)
        n_employees = 1470
        departments = ['Research & Development', 'Sales', 'Human Resources']
        dept_probs = [0.65, 0.30, 0.05]
        genders = ['Male', 'Female']
        gender_probs = [0.60, 0.40]
        job_roles = {
            'Research & Development': ['Research Scientist', 'Laboratory Technician', 'Manufacturing Director', 'Healthcare Representative', 'Research Director', 'Manager'],
            'Sales': ['Sales Executive', 'Sales Representative', 'Manager'],
            'Human Resources': ['Human Resources', 'Manager']
        }
        data = []
        for i in range(n_employees):
            dept = np.random.choice(departments, p=dept_probs)
            role = np.random.choice(job_roles[dept])
            gender = np.random.choice(genders, p=gender_probs)
            age = np.random.normal(37, 9).clip(18, 60).astype(int)
            
            if 'Director' in role or role == 'Manager': income = np.random.normal(15000, 3000)
            elif 'Representative' in role or role == 'Sales Executive': income = np.random.normal(6000, 2000)
            else: income = np.random.normal(5000, 2000)
            income = max(1000, income)
            
            years_at_co = np.random.exponential(5)
            if years_at_co > 30: years_at_co = np.random.uniform(20, 30)
            
            overtime = np.random.choice(['Yes', 'No'], p=[0.28, 0.72])
            travel = np.random.choice(['Travel_Rarely', 'Travel_Frequently', 'Non-Travel'], p=[0.7, 0.18, 0.12])
            distance = np.random.choice([1, 5, 10, 15, 20, 25], p=[0.3, 0.2, 0.2, 0.15, 0.1, 0.05])
            
            attrition_prob = 0.10
            if overtime == 'Yes': attrition_prob += 0.15
            if travel == 'Travel_Frequently': attrition_prob += 0.10
            if income < 4000: attrition_prob += 0.15
            if 1 <= years_at_co <= 3: attrition_prob += 0.10
            if 26 <= age <= 35: attrition_prob += 0.05
            
            attrition = 'Yes' if np.random.random() < attrition_prob else 'No'
            
            data.append({
                'Age': age, 'Department': dept, 'Gender': gender, 'JobRole': role,
                'MonthlyIncome': round(income, 2), 'YearsAtCompany': round(years_at_co, 1),
                'OverTime': overtime, 'BusinessTravel': travel, 'DistanceFromHome': distance,
                'JobSatisfaction': np.random.randint(1, 5), 'EnvironmentSatisfaction': np.random.randint(1, 5),
                'WorkLifeBalance': np.random.randint(1, 5), 'Attrition': attrition
            })
        df = pd.DataFrame(data)

    # Feature Engineering (Works for both Real CSV and Mock Data)
    df['AttritionNum'] = (df['Attrition'] == 'Yes').astype(int)
    df['AgeGroup'] = pd.cut(df['Age'], bins=[17, 25, 35, 45, 55, 100], labels=['18-25', '26-35', '36-45', '46-55', '56+'])
    df['IncomeBand'] = pd.cut(df['MonthlyIncome'], bins=[0, 3000, 6000, 10000, 50000], labels=['<$3K', '$3K-$6K', '$6K-$10K', '$10K+'])
    df['TenureGroup'] = pd.cut(df['YearsAtCompany'], bins=[-0.1, 1, 3, 5, 10, 100], labels=['<1 Yr', '1-3 Yrs', '3-5 Yrs', '5-10 Yrs', '10+ Yrs'])
    
    return df

df_raw = load_data()

# ==========================================
# 3. SIDEBAR FILTERS (CENTRALIZED STATE)
# ==========================================
with st.sidebar:
    st.markdown("### 🎛️ Global Filters")
    st.markdown("Adjust filters to dynamically slice all dashboard tabs.")
    st.markdown("---")
    
    dept_filter = st.multiselect("Department", options=df_raw['Department'].unique(), default=df_raw['Department'].unique())
    gender_filter = st.multiselect("Gender", options=df_raw['Gender'].unique(), default=df_raw['Gender'].unique())
    age_filter = st.multiselect("Age Group", options=df_raw['AgeGroup'].cat.categories, default=df_raw['AgeGroup'].cat.categories)
    income_filter = st.multiselect("Income Band", options=df_raw['IncomeBand'].cat.categories, default=df_raw['IncomeBand'].cat.categories)
    tenure_filter = st.multiselect("Tenure Group", options=df_raw['TenureGroup'].cat.categories, default=df_raw['TenureGroup'].cat.categories)
    
    st.markdown("---")
    if st.button("🔄 Reset Filters", use_container_width=True):
        st.session_state.clear()
        st.rerun()

# Apply Filters to Central DataFrame
df = df_raw[
    (df_raw['Department'].isin(dept_filter)) &
    (df_raw['Gender'].isin(gender_filter)) &
    (df_raw['AgeGroup'].isin(age_filter)) &
    (df_raw['IncomeBand'].isin(income_filter)) &
    (df_raw['TenureGroup'].isin(tenure_filter))
].copy()

# ==========================================
# 4. PLOTLY STYLING HELPERS
# ==========================================
PLOTLY_LAYOUT = {
    'paper_bgcolor': 'rgba(0,0,0,0)',
    'plot_bgcolor': 'rgba(0,0,0,0)',
    'font': dict(color='#f8fafc', size=12),
    'margin': dict(l=20, r=20, t=40, b=20),
    'xaxis': dict(gridcolor='#334155', zerolinecolor='#334155'),
    'yaxis': dict(gridcolor='#334155', zerolinecolor='#334155'),
}

def create_chart(fig, height=350):
    fig.update_layout(**PLOTLY_LAYOUT, height=height, template="plotly_dark")
    fig.update_traces(hovertemplate='<b>%{x}</b><br>Value: %{y}<extra></extra>')
    return fig

# ==========================================
# 5. MAIN DASHBOARD TABS
# ==========================================
st.markdown("<h1 style='margin-bottom: 0px;'>HR Attrition Analytics Dashboard</h1>", unsafe_allow_html=True)
st.markdown("<p style='color: #94a3b8; margin-top: 0px;'>Workforce Turnover, Root Causes & Financial Impact</p>", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["Executive Summary", "Root Cause Analysis", "Financial Impact"])

# ------------------------------
# TAB 1: EXECUTIVE SUMMARY
# ------------------------------
with tab1:
    c1, c2, c3, c4, c5 = st.columns(5)
    total_emp = len(df)
    attrition_rate = (df['AttritionNum'].sum() / total_emp) * 100 if total_emp > 0 else 0
    avg_income = df['MonthlyIncome'].mean() if total_emp > 0 else 0
    avg_tenure = df['YearsAtCompany'].mean() if total_emp > 0 else 0
    overtime_rate = (df[df['OverTime'] == 'Yes'].shape[0] / total_emp) * 100 if total_emp > 0 else 0
    
    with c1: st.metric("Total Employees", f"{total_emp:,}")
    with c2: st.metric("Attrition Rate", f"{attrition_rate:.1f}%", delta=f"{df['AttritionNum'].sum()} Left", delta_color="inverse")
    with c3: st.metric("Avg Monthly Income", f"${avg_income:,.0f}")
    with c4: st.metric("Avg Tenure", f"{avg_tenure:.1f} yrs")
    with c5: st.metric("Overtime Rate", f"{overtime_rate:.1f}%")
        
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("##### Attrition by Department")
        dept_df = df.groupby('Department')['AttritionNum'].sum().reset_index()
        fig = px.bar(dept_df, x='Department', y='AttritionNum', color='Department', color_discrete_sequence=['#3b82f6', '#14b8a6', '#f59e0b'])
        st.plotly_chart(create_chart(fig), use_container_width=True)
        
    with col2:
        st.markdown("##### Attrition by Age Group")
        age_df = df.groupby('AgeGroup')['AttritionNum'].sum().reset_index()
        fig = px.bar(age_df, x='AgeGroup', y='AttritionNum', color_discrete_sequence=['#8b5cf6'])
        st.plotly_chart(create_chart(fig), use_container_width=True)
        
    with col3:
        st.markdown("##### Gender Distribution")
        gen_df = df.groupby('Gender').size().reset_index(name='Counts')
        fig = px.pie(gen_df, values='Counts', names='Gender', hole=0.4, color='Gender', color_discrete_map={'Male': '#3b82f6', 'Female': '#14b8a6'})
        fig.update_traces(textfont_color='white')
        st.plotly_chart(create_chart(fig), use_container_width=True)
        
    col4, col5, col6 = st.columns(3)
    with col4:
        st.markdown("##### Attrition by Job Role")
        role_df = df.groupby('JobRole')['AttritionNum'].sum().reset_index().sort_values(by='AttritionNum', ascending=True)
        fig = px.bar(role_df, x='AttritionNum', y='JobRole', orientation='h', color_discrete_sequence=['#ef4444'])
        st.plotly_chart(create_chart(fig), use_container_width=True)
        
    with col5:
        st.markdown("##### Attrition by Income Band")
        inc_df = df.groupby('IncomeBand')['AttritionNum'].sum().reset_index()
        fig = px.bar(inc_df, x='IncomeBand', y='AttritionNum', color_discrete_sequence=['#10b981'])
        st.plotly_chart(create_chart(fig), use_container_width=True)
        
    with col6:
        st.markdown("##### Attrition by Tenure")
        ten_df = df.groupby('TenureGroup')['AttritionNum'].sum().reset_index()
        fig = px.bar(ten_df, x='TenureGroup', y='AttritionNum', color_discrete_sequence=['#f59e0b'])
        st.plotly_chart(create_chart(fig), use_container_width=True)

# ------------------------------
# TAB 2: ROOT CAUSE ANALYSIS
# ------------------------------
with tab2:
    st.markdown("##### Workplace Factors Driving Attrition")
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown("###### Attrition by OverTime")
        ot_df = df.groupby('OverTime').agg(Total=('AttritionNum', 'count'), Left=('AttritionNum', 'sum')).reset_index()
        ot_df['Rate'] = (ot_df['Left'] / ot_df['Total']) * 100
        fig = px.bar(ot_df, x='OverTime', y='Rate', color='OverTime', color_discrete_sequence=['#10b981', '#ef4444'])
        st.plotly_chart(create_chart(fig), use_container_width=True)
        
    with c2:
        st.markdown("###### Attrition by Business Travel")
        trv_df = df.groupby('BusinessTravel').agg(Total=('AttritionNum', 'count'), Left=('AttritionNum', 'sum')).reset_index()
        trv_df['Rate'] = (trv_df['Left'] / trv_df['Total']) * 100
        fig = px.bar(trv_df, x='BusinessTravel', y='Rate', color='BusinessTravel', color_discrete_sequence=['#10b981', '#f59e0b', '#ef4444'])
        st.plotly_chart(create_chart(fig), use_container_width=True)
        
    with c3:
        st.markdown("###### Attrition by Distance from Home")
        df['DistBin'] = pd.cut(df['DistanceFromHome'], bins=[0, 5, 10, 20, 30], labels=['1-5km', '6-10km', '11-20km', '21km+'])
        dist_df = df.groupby('DistBin').agg(Total=('AttritionNum', 'count'), Left=('AttritionNum', 'sum')).reset_index()
        dist_df['Rate'] = (dist_df['Left'] / dist_df['Total']) * 100
        fig = px.bar(dist_df, x='DistBin', y='Rate', color_discrete_sequence=['#8b5cf6'])
        st.plotly_chart(create_chart(fig), use_container_width=True)

    st.markdown("---")
    
    st.markdown("##### Employee Satisfaction Metrics (Rate of Attrition)")
    c4, c5, c6 = st.columns(3)
    
    with c4:
        st.markdown("###### Job Satisfaction")
        js_df = df.groupby('JobSatisfaction').agg(Total=('AttritionNum', 'count'), Left=('AttritionNum', 'sum')).reset_index()
        js_df['Rate'] = (js_df['Left'] / js_df['Total']) * 100
        fig = px.bar(js_df, x='JobSatisfaction', y='Rate', color_discrete_sequence=['#3b82f6'])
        fig.update_layout(xaxis_title="Level (1=Low, 4=High)")
        st.plotly_chart(create_chart(fig), use_container_width=True)
        
    with c5:
        st.markdown("###### Environment Satisfaction")
        es_df = df.groupby('EnvironmentSatisfaction').agg(Total=('AttritionNum', 'count'), Left=('AttritionNum', 'sum')).reset_index()
        es_df['Rate'] = (es_df['Left'] / es_df['Total']) * 100
        fig = px.bar(es_df, x='EnvironmentSatisfaction', y='Rate', color_discrete_sequence=['#14b8a6'])
        fig.update_layout(xaxis_title="Level (1=Low, 4=High)")
        st.plotly_chart(create_chart(fig), use_container_width=True)
        
    with c6:
        st.markdown("###### Work-Life Balance")
        wlb_df = df.groupby('WorkLifeBalance').agg(Total=('AttritionNum', 'count'), Left=('AttritionNum', 'sum')).reset_index()
        wlb_df['Rate'] = (wlb_df['Left'] / wlb_df['Total']) * 100
        fig = px.bar(wlb_df, x='WorkLifeBalance', y='Rate', color_discrete_sequence=['#f59e0b'])
        fig.update_layout(xaxis_title="Level (1=Bad, 4=Good)")
        st.plotly_chart(create_chart(fig), use_container_width=True)

# ------------------------------
# TAB 3: FINANCIAL IMPACT
# ------------------------------
with tab3:
    REPLACEMENT_COST = 39020  # External business logic from Power BI report
    
    reduction_pct = st.slider("🎯 What-If Analysis: Target Attrition Reduction (%)", 0, 30, 10, step=1)
    
    total_left = df['AttritionNum'].sum()
    current_cost = total_left * REPLACEMENT_COST
    projected_savings = current_cost * (reduction_pct / 100)
    projected_new_cost = current_cost - projected_savings
    
    fc1, fc2, fc3, fc4 = st.columns(4)
    with fc1: st.metric("Current Attrition Cost", f"${current_cost:,.0f}")
    with fc2: st.metric("Avg Replacement Cost", f"${REPLACEMENT_COST:,.0f}")
    with fc3: st.metric("Employees Lost", f"{total_left}")
    with fc4: st.metric("Projected Savings", f"${projected_savings:,.0f}", delta=f"-{reduction_pct}% Target", delta_color="off")
        
    st.markdown("---")
    
    fc5, fc6 = st.columns(2)
    with fc5:
        st.markdown("##### Attrition Cost by Department")
        cost_df = df.groupby('Department')['AttritionNum'].sum().reset_index()
        cost_df['Cost'] = cost_df['AttritionNum'] * REPLACEMENT_COST
        fig = px.bar(cost_df, x='Cost', y='Department', orientation='h', color='Department', color_discrete_sequence=['#3b82f6', '#14b8a6', '#f59e0b'])
        fig.update_xaxes(title="Estimated Cost ($)")
        st.plotly_chart(create_chart(fig), use_container_width=True)
        
    with fc6:
        st.markdown("##### Cost Breakdown")
        labels = ['Recruitment', 'Productivity Loss', 'Training']
        values = [0.40 * current_cost, 0.35 * current_cost, 0.25 * current_cost]
        fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=0.4, marker_colors=['#3b82f6', '#f59e0b', '#ef4444'])])
        fig.update_traces(textfont_color='white')
        st.plotly_chart(create_chart(fig), use_container_width=True)
        
    st.markdown("---")
    
    st.markdown("##### 🚀 Recommended Actions")
    rc1, rc2, rc3 = st.columns(3)
    
    with rc1:
        st.markdown("""
        <div class="insight-box">
            <h4>Priority 1: Reduce Overtime</h4>
            <p>Overtime is the strongest predictor of attrition. Caps and redistribution in R&D and Sales will yield the highest cost savings.</p>
        </div>
        """, unsafe_allow_html=True)
        
    with rc2:
        st.markdown("""
        <div class="insight-box" style="border-left-color: #f59e0b;">
            <h4 style="color: #f59e0b;">Priority 2: Career Development</h4>
            <p>Employees aged 26-35 and 1-3 year tenure are leaving most. Strengthen pathing and mentoring for this cohort.</p>
        </div>
        """, unsafe_allow_html=True)
        
    with rc3:
        st.markdown("""
        <div class="insight-box" style="border-left-color: #10b981;">
            <h4 style="color: #10b981;">Priority 3: Compensation Review</h4>
            <p>Review salaries for employees earning <$3K/month. This group represents nearly 50% of all attrition.</p>
        </div>
        """, unsafe_allow_html=True)
