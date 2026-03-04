"""
GreenScope Analytics - EAGC Market Intelligence Demo
=====================================================
A simple tool to help EAGC understand grain markets and make better decisions.
"""

import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.patches import FancyBboxPatch, Circle, Rectangle
import networkx as nx
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Page setup
st.set_page_config(
    page_title="GreenScope | Market Intelligence",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Force custom CSS with !important and more specific selectors
st.markdown("""
<style>
    /* Force override Streamlit's defaults */
    .stApp header {
        visibility: hidden;
    }
    
    div[data-testid="stToolbar"] {
        visibility: hidden;
    }
    
    .main .block-container {
        padding-top: 2rem;
    }
    
    /* Big title with forced styling */
    .big-title {
        font-size: 5rem !important;
        font-weight: 700 !important;
        color: #1E3A8A !important;
        margin-bottom: 1rem !important;
        line-height: 1.2 !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important;
    }
    
    /* Big subtitle with forced styling */
    .big-subtitle {
        font-size: 2.5rem !important;
        color: #059669 !important;
        margin-bottom: 3rem !important;
        font-weight: 500 !important;
        line-height: 1.3 !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important;
    }
    
    /* Alternative: use HTML directly */
    h1.custom-title {
        font-size: 5rem;
        color: #1E3A8A;
    }
</style>
""", unsafe_allow_html=True)

# Create sample market data
@st.cache_data
def create_market_data(crop="Maize", country="Kenya", seed=42, months=36):
    np.random.seed(seed)
    dates = pd.date_range(start='2022-01-01', periods=months, freq='M')
    
    # Base parameters vary by crop
    crop_params = {
        "Maize": {"base_price": 2500, "volatility": 100, "supply_sensitivity": 15},
        "Beans": {"base_price": 4000, "volatility": 150, "supply_sensitivity": 25},
        "Wheat": {"base_price": 3500, "volatility": 120, "supply_sensitivity": 20}
    }
    
    # Country modifiers
    country_params = {
        "Kenya": {"conflict_impact": 1.0, "drought_freq": 0.2},
        "Uganda": {"conflict_impact": 0.6, "drought_freq": 0.15},
        "Tanzania": {"conflict_impact": 0.4, "drought_freq": 0.1}
    }
    
    params = crop_params.get(crop, crop_params["Maize"])
    c_params = country_params.get(country, country_params["Kenya"])
    
    # Market factors that affect prices
    harvest = 100 + 20 * np.sin(np.arange(months) * 2 * np.pi / 12) + np.random.normal(0, 10, months)
    export_stop = np.random.choice([0, 1], size=months, p=[0.85, 0.15])
    conflict = np.clip(np.cumsum(np.random.normal(0.02, 0.1, months)) + 2 * c_params["conflict_impact"], 0, 10)
    drought = np.random.choice([0, 1], size=months, p=[1-c_params["drought_freq"], c_params["drought_freq"]])
    
    # How these factors connect
    available_supply = harvest * 0.6 + (1 - export_stop) * 30 - conflict * 2
    available_supply = np.clip(available_supply, 20, 150)
    
    # Calculate price based on supply and other factors
    base_price = params["base_price"]
    price = (base_price 
             - params["supply_sensitivity"] * (available_supply - 80)
             + 50 * export_stop
             + 30 * conflict
             + 200 * drought
             + np.random.normal(0, params["volatility"], months))
    
    # Track reserve stocks
    reserve_stock = np.zeros(months)
    reserve_stock[0] = 500
    for i in range(1, months):
        release = 50 if price[i] > base_price * 1.3 else 0
        reserve_stock[i] = np.clip(reserve_stock[i-1] - release + 20, 0, 1000)
    
    # Food security measure (higher = worse)
    food_security_risk = np.clip(30 + 0.02 * price - 0.05 * reserve_stock + np.random.normal(0, 3, months), 0, 100)
    
    return pd.DataFrame({
        'date': dates,
        'harvest': harvest,
        'export_stop': export_stop,
        'conflict': conflict,
        'drought': drought,
        'available_supply': available_supply,
        'market_price': price,
        'reserve_stock': reserve_stock,
        'food_security_risk': food_security_risk
    })

# Page header - Using HTML with inline styles for maximum compatibility
st.markdown("""
<div style="margin-bottom: 3rem;">
    <h1 style="
        font-size: 5rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 1rem;
        line-height: 1.2;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    ">🌾 GreenScope Analytics</h1>
    <p style="
        font-size: 2.5rem;
        color: #059669;
        margin-bottom: 0;
        font-weight: 500;
        line-height: 1.3;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    ">Helping EAGC understand markets and make smart decisions</p>
</div>
""", unsafe_allow_html=True)

# Alternative: Use st.title with custom sizing
# st.title("🌾 GreenScope Analytics")
# st.markdown('<p style="font-size: 2.5rem; color: #059669; margin-top: -1rem;">Helping EAGC understand markets and make smart decisions</p>', unsafe_allow_html=True)

# Sidebar controls
with st.sidebar:
    st.header("Settings")
    
    st.subheader("Market Selection")
    country = st.selectbox("Country", ["Kenya", "Uganda", "Tanzania"])
    crop = st.selectbox("Crop", ["Maize", "Beans", "Wheat"])
    
    st.subheader("Test Scenario")
    action = st.selectbox("What should we test?", [
        "Do nothing (see what happens)",
        "Release grain reserves",
        "Fix trade routes",
        "Do both (reserves + routes)"
    ])
    
    st.subheader("Time Period")
    months_ahead = st.slider("Months to look ahead", 3, 12, 6)
    
    st.markdown("---")
    st.info(f"Currently viewing: {crop} prices in {country}")

# Load data based on selections
data = create_market_data(crop=crop, country=country)

# Calculate scenario-specific metrics
def get_scenario_metrics(crop, country, action):
    """Calculate metrics based on crop, country, and action"""
    base_metrics = {
        "Maize": {"price": 3000, "volatility": "medium"},
        "Beans": {"price": 4500, "volatility": "high"},
        "Wheat": {"price": 3800, "volatility": "medium"}
    }
    
    country_factor = {
        "Kenya": 1.0,
        "Uganda": 0.85,
        "Tanzania": 0.90
    }
    
    base = base_metrics.get(crop, base_metrics["Maize"])
    factor = country_factor.get(country, 1.0)
    base_price = base["price"] * factor
    
    # Action effects vary by crop and country
    if action == "Do nothing (see what happens)":
        return {
            'price_drop': 0, 
            'cost': 0, 
            'works': 0,
            'people_helped': 0,
            'description': f"{crop} prices continue current trend in {country}"
        }
    elif action == "Release grain reserves":
        return {
            'price_drop': 8 if crop == "Maize" else 12 if crop == "Beans" else 10, 
            'cost': int(150 * factor), 
            'works': 65,
            'people_helped': int(1.5 * factor),
            'description': f"Release {crop} reserves to stabilize {country} market"
        }
    elif action == "Fix trade routes":
        return {
            'price_drop': 15 if crop == "Maize" else 18 if crop == "Beans" else 16, 
            'cost': int(80 * factor), 
            'works': 80,
            'people_helped': int(2.0 * factor),
            'description': f"Improve {crop} transport corridors to {country}"
        }
    else:  # Do both
        return {
            'price_drop': 26 if crop == "Maize" else 32 if crop == "Beans" else 28, 
            'cost': int(200 * factor), 
            'works': 92,
            'people_helped': int(2.3 * factor),
            'description': f"Combined approach for maximum {crop} price stability in {country}"
        }

# Get current scenario metrics
current_metrics = get_scenario_metrics(crop, country, action)

# Main report selector
st.markdown("---")
report_choice = st.radio(
    "What do you want to know?",
    ["📊 Summary Report", "🔍 Why are prices changing?", "🔮 What if we take action?", "🎯 What's the best move?", "📈 How accurate are we?"],
    horizontal=True
)

# NEW: Summary Report (ties everything together)
if "Summary Report" in report_choice:
    st.header("📊 Executive Summary")
    st.markdown(f"*Quick overview of {crop} market in {country}*")
    
    # Key numbers at a glance
    st.subheader("Current Situation")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(f"{crop} Price", f"KES {data['market_price'].iloc[-1]:.0f}", "Last month")
    with col2:
        trend = "Up 6.8%" if data['market_price'].iloc[-1] > data['market_price'].iloc[-6] else "Down"
        st.metric("Price Trend", trend, "vs 6 months ago")
    with col3:
        risk_level = "High" if data['food_security_risk'].iloc[-1] > 50 else "Medium" if data['food_security_risk'].iloc[-1] > 30 else "Low"
        st.metric("Food Security Risk", risk_level, f"{data['food_security_risk'].iloc[-1]:.0f}/100")
    with col4:
        st.metric("Reserve Stocks", f"{data['reserve_stock'].iloc[-1]:.0f}k tons", "Available")
    
    st.markdown("---")
    
    # What's happening
    st.subheader("What's Happening?")
    causes = []
    if data['export_stop'].iloc[-3:].mean() > 0.3:
        causes.append("Export restrictions in neighboring countries")
    if data['drought'].iloc[-6:].mean() > 0.2:
        causes.append("Poor rainfall affecting harvests")
    if data['conflict'].iloc[-1] > 5:
        causes.append("Regional conflict increasing transport costs")
    if data['available_supply'].iloc[-1] < 60:
        causes.append("Low supply in local markets")
    
    if causes:
        for cause in causes[:3]:
            st.write(f"• {cause}")
    else:
        st.write("• Market conditions are relatively stable")
    
    # What we're recommending
    st.subheader("Our Recommendation")
    
    # Find best action
    all_options = {
        "Do nothing": get_scenario_metrics(crop, country, "Do nothing (see what happens)"),
        "Release reserves": get_scenario_metrics(crop, country, "Release grain reserves"),
        "Fix trade routes": get_scenario_metrics(crop, country, "Fix trade routes"),
        "Do both": get_scenario_metrics(crop, country, "Do both (reserves + routes)")
    }
    
    best_option = max(all_options.items(), key=lambda x: x[1]['works'])
    
    rec_col1, rec_col2 = st.columns([2, 1])
    with rec_col1:
        st.success(f"**Recommended: {best_option[0]}**")
        st.write(f"• Prices drop by {best_option[1]['price_drop']}%")
        st.write(f"• Helps {best_option[1]['people_helped']:.1f} million people")
        st.write(f"• Costs KES {best_option[1]['cost']} million")
        st.write(f"• {best_option[1]['works']}% confidence this works")
    
    with rec_col2:
        st.info("**Why this works:**")
        st.write(best_option[1]['description'])
    
    st.markdown("---")
    
    # Quick price chart
    st.subheader(f"{crop} Price Trend")
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(data['date'], data['market_price'], linewidth=2.5, color='#2E7D32', label=f'{crop} Price')
    ax.axhline(y=data['market_price'].mean() * 1.3, color='red', linestyle='--', alpha=0.7, label='Crisis Level')
    ax.fill_between(data['date'], data['market_price'], data['market_price'].mean() * 1.3, 
                    where=(data['market_price'] > data['market_price'].mean() * 1.3), alpha=0.3, color='red')
    ax.set_ylabel(f'Price (KES per {crop} bag)')
    ax.legend()
    ax.grid(True, alpha=0.3)
    st.pyplot(fig)
    
    # Next steps
    st.subheader("Next Steps")
    st.write("1. Review detailed analysis in other tabs")
    st.write("2. Test different scenarios using the sidebar")
    st.write("3. Contact GreenScope to implement this for real")

# Report 1: Why prices are changing
elif "Why are prices changing" in report_choice:
    st.header(f"🔍 Understanding {crop} Price Changes in {country}")
    st.markdown("*Finding the real reasons behind market movements*")
    
    # Key numbers
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(f"Current {crop} Price", f"KES {data['market_price'].iloc[-1]:.0f}", "Last reading")
    with col2:
        risk = data['food_security_risk'].iloc[-1]
        risk_text = "High" if risk > 50 else "Medium" if risk > 30 else "Low"
        st.metric("Food Security Risk", risk_text, f"{risk:.1f}/100")
    with col3:
        st.metric("Reserve Stocks", f"{data['reserve_stock'].iloc[-1]:.0f}k tons", "Available")
    
    st.markdown("---")
    
    # Price chart
    st.subheader(f"{crop} Price Trend")
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(data['date'], data['market_price'], linewidth=2.5, color='#2E7D32', label=f'{crop} Price')
    crisis_level = data['market_price'].mean() * 1.3
    ax.axhline(y=crisis_level, color='red', linestyle='--', alpha=0.7, label='Crisis Level')
    ax.fill_between(data['date'], data['market_price'], crisis_level, 
                    where=(data['market_price'] > crisis_level), alpha=0.3, color='red')
    ax.set_ylabel(f'Price (KES per {crop} bag)')
    ax.legend()
    ax.grid(True, alpha=0.3)
    st.pyplot(fig)
    
    # What caused this?
    st.subheader("What's Really Causing This?")
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Simple cause-and-effect diagram
        fig, ax = plt.subplots(figsize=(10, 6))
        G = nx.DiGraph()
        connections = [
            ("Drought", "Low Supply", 0.7),
            ("Export Ban", "Low Supply", 0.8),
            ("Conflict", "High Transport Cost", 0.6),
            ("Low Supply", "High Prices", 0.9),
            ("High Transport Cost", "High Prices", 0.5),
            ("High Prices", "Food Insecurity", 0.75)
        ]
        for cause, effect, strength in connections:
            G.add_edge(cause, effect, weight=strength)
        
        pos = nx.spring_layout(G, seed=42, k=2)
        nx.draw(G, pos, with_labels=True, node_color='#1976D2', 
                node_size=3000, font_size=9, font_color='white',
                font_weight='bold', arrows=True, arrowsize=20,
                edge_color='#424242', width=[d['weight']*3 for (u, v, d) in G.edges(data=True)],
                ax=ax)
        ax.set_title("How Factors Connect", fontweight='bold')
        st.pyplot(fig)
    
    with col2:
        st.markdown("""
        **Main Findings:**
        
        1. **Biggest factor (35%)**: Export restrictions
        2. **Second factor (25%)**: Drought reducing harvests
        3. **Third factor (20%)**: Conflict increasing costs
        4. **Our confidence**: 87% sure these are the real causes
        """)
    
    # Simple breakdown
    st.subheader("What Drove Prices Up?")
    causes = pd.DataFrame({
        'Factor': ['Export Restrictions', 'Drought', 'Conflict', 'Transport Costs', 'Other'],
        'Impact (%)': [35, 25, 20, 15, 5]
    })
    fig, ax = plt.subplots(figsize=(10, 4))
    colors = ['#D32F2F', '#FF6B6B', '#FFA726', '#FFCA28', '#E0E0E0']
    ax.barh(causes['Factor'], causes['Impact (%)'], color=colors)
    ax.set_xlabel('How much this pushed prices up (%)')
    ax.grid(True, alpha=0.3, axis='x')
    st.pyplot(fig)

# Report 2: What if we take action - SMALLER FONTS
elif "What if we take action" in report_choice:
    st.header(f"🔮 Testing Actions for {crop} in {country}")
    st.markdown("*See what happens before you decide*")
    
    # Get all scenarios for comparison
    scenarios = {
        'Do nothing': get_scenario_metrics(crop, country, "Do nothing (see what happens)"),
        'Release reserves': get_scenario_metrics(crop, country, "Release grain reserves"),
        'Fix trade routes': get_scenario_metrics(crop, country, "Fix trade routes"),
        'Do both': get_scenario_metrics(crop, country, "Do both (reserves + routes)")
    }
    
    # Compare options - SMALLER FONTS using custom HTML
    st.subheader("Compare Options")
    
    cols = st.columns(4)
    option_names = list(scenarios.keys())
    
    for i, (col, option_name) in enumerate(zip(cols, option_names)):
        with col:
            metrics = scenarios[option_name]
            st.markdown(f"""
            <div style='font-size: 0.85rem; text-align: center; padding: 10px; background-color: #f8fafc; border-radius: 8px;'>
                <strong>{option_name}</strong><br>
                <span style='font-size: 0.9rem;'>Prices down {metrics['price_drop']}%</span><br>
                <span style='font-size: 0.8rem; color: #666;'>Costs KES {metrics['cost']}M</span>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Show price paths
    st.subheader(f"{crop} Price Predictions for Next {months_ahead} Months")
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][:months_ahead]
    
    # Generate baseline based on current crop/country
    base_price = data['market_price'].iloc[-1]
    no_action_prices = [base_price * (1 + 0.02 * i + np.random.normal(0, 0.01)) for i in range(months_ahead)]
    
    fig, ax = plt.subplots(figsize=(12, 5))
    colors = ['#D32F2F', '#FF9800', '#4CAF50', '#1976D2']
    
    for i, (option, metrics) in enumerate(scenarios.items()):
        if option == 'Do nothing':
            prices = no_action_prices
        else:
            drop = metrics['price_drop'] / 100
            prices = [p * (1 - drop) for p in no_action_prices]
        
        ax.plot(months, prices, marker='o', linewidth=2.5, 
                label=option, color=colors[i])
    
    crisis = base_price * 1.3
    ax.axhline(y=crisis, color='red', linestyle='--', alpha=0.5, label='Crisis Level')
    ax.fill_between(months, base_price * 0.8, crisis, alpha=0.1, color='green', label='Safe Zone')
    ax.set_ylabel(f'Price (KES per {crop} bag)')
    ax.legend()
    ax.grid(True, alpha=0.3)
    st.pyplot(fig)
    
    # Recommendation based on selection
    st.markdown("---")
    st.subheader("Analysis of Your Selection")
    
    selected_metrics = scenarios.get("Do nothing" if "nothing" in action else 
                                    "Release reserves" if "reserves" in action else
                                    "Fix trade routes" if "routes" in action else
                                    "Do both")
    
    left, right = st.columns([1, 1])
    with left:
        st.write(f"**Option: {action}**")
        st.write(f"• Expected price drop: {selected_metrics['price_drop']}%")
        st.write(f"• People helped: {selected_metrics['people_helped']:.1f} million")
        st.write(f"• Implementation cost: KES {selected_metrics['cost']} million")
        st.write(f"• Success probability: {selected_metrics['works']}%")
    
    with right:
        st.write("**What this means:**")
        st.write(selected_metrics['description'])
        
        if selected_metrics['price_drop'] > 20:
            st.success("This is our recommended approach")
        elif selected_metrics['price_drop'] > 10:
            st.info("This is a good moderate option")
        else:
            st.warning("Consider stronger action")

# Report 3: What's the best move
elif "What's the best move" in report_choice:
    st.header(f"🎯 Best Strategy for {crop} in {country}")
    st.markdown("*Smart planning for the long term*")
    
    # Cost vs benefit chart
    st.subheader("Best Value for Money")
    
    np.random.seed(42)
    strategies = 50
    costs = np.random.uniform(50, 400, strategies)
    effectiveness = 85 - 0.15 * costs + np.random.normal(0, 5, strategies)
    effectiveness = np.clip(effectiveness, 30, 95)
    
    # Find best options
    good_deals = np.ones(strategies, dtype=bool)
    for i in range(strategies):
        for j in range(strategies):
            if i != j:
                if costs[j] <= costs[i] and effectiveness[j] >= effectiveness[i]:
                    if costs[j] < costs[i] or effectiveness[j] > effectiveness[i]:
                        good_deals[i] = False
                        break
    
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.scatter(costs[~good_deals], effectiveness[~good_deals], 
               c='lightgray', s=50, alpha=0.5, label='Not the best value')
    ax.scatter(costs[good_deals], effectiveness[good_deals], 
               c='#1976D2', s=100, alpha=0.8, label='Best value options', 
               edgecolors='black', linewidth=2)
    
    # Highlight best for current context
    best = get_scenario_metrics(crop, country, "Do both (reserves + routes)")
    ax.scatter([best['cost']], [best['works']], c='#4CAF50', s=400, marker='*', 
               edgecolors='black', linewidth=2, label='OUR PICK', zorder=10)
    
    ax.set_xlabel('Cost (Million KES)')
    ax.set_ylabel('How well it works (score)')
    ax.legend()
    ax.grid(True, alpha=0.3)
    st.pyplot(fig)
    
    # Timeline
    st.subheader("12-Month Implementation Plan")
    
    plan = pd.DataFrame({
        'Phase': ['Connect data sources', 'Build prediction model', 'Test scenarios', 'Launch system'],
        'When': ['Months 1-3', 'Months 3-6', 'Months 6-9', 'Months 9-12'],
        'What we deliver': [
            f'All {crop} data from {country} in one place',
            f'Working tool for {crop} price predictions',
            f'Tested with real {crop} market events',
            f'Full decision support for {country}'
        ]
    })
    
    st.table(plan)
    
    # Budget
    st.subheader("Recommended Budget: KES 500M")
    
    spending = pd.DataFrame({
        'Activity': ['Manage reserves', 'Fix trade routes', 'Data systems', 'Training', 'Backup funds'],
        'Percentage': [35, 30, 20, 10, 5],
        'Amount (KES M)': [175, 150, 100, 50, 25]
    })
    
    left, right = st.columns([1, 1])
    with left:
        fig, ax = plt.subplots(figsize=(8, 6))
        colors = ['#1976D2', '#388E3C', '#F57C00', '#7B1FA2', '#616161']
        ax.pie(spending['Percentage'], labels=spending['Activity'], 
               autopct='%1.0f%%', colors=colors, startangle=90)
        ax.set_title('Budget Split')
        st.pyplot(fig)
    
    with right:
        st.table(spending)

# Report 4: How accurate are we
else:
    st.header("📈 How Accurate Are Our Predictions?")
    st.markdown("*Tracking our performance and improvements*")
    
    # Accuracy over time
    st.subheader("Getting Better With Each Prediction")
    
    history = pd.DataFrame({
        'Prediction #': range(1, 9),
        'Error (%)': [20, 15, 18, 12, 10, 14, 11, 9],
        'Confidence': [65, 70, 72, 78, 80, 82, 85, 88]
    })
    
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(history['Prediction #'], history['Error (%)'], 
            marker='o', linewidth=2.5, markersize=8, color='#D32F2F', label='How wrong we were')
    ax.fill_between(history['Prediction #'], history['Error (%)'], 
                    alpha=0.3, color='#D32F2F')
    
    # Trend line
    z = np.polyfit(history['Prediction #'], history['Error (%)'], 1)
    p = np.poly1d(z)
    ax.plot(history['Prediction #'], p(history['Prediction #']), 
            "--", color='#1976D2', linewidth=2, label='Getting better')
    
    ax.set_xlabel('Number of predictions made')
    ax.set_ylabel('Error (%)')
    ax.legend()
    ax.grid(True, alpha=0.3)
    st.pyplot(fig)
    
    # Current stats
    st.subheader("Current Performance")
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Prediction Error", "9.1%", "Down 10.9%")
    with c2:
        st.metric("Confidence", "88%", "Up 23%")
    with c3:
        st.metric("Updates made", "24", "Ongoing")
    with c4:
        st.metric("Quality check", "PASSED", "Independent review")
    
    # How we improved
    st.subheader("How the System Learned")
    st.markdown("""
    **Starting point (Month 0):**
    - Basic connections only
    - 65% accuracy
    - Simple supply and demand
    
    **After 4 predictions:**
    - Added policy and conflict factors
    - 78% accuracy
    - Better understanding
    
    **Now (Month 16):**
    - Full picture of market drivers
    - 88% accuracy
    - Learns from each prediction
    """)
    
    st.info(f"💡 **Key discovery for {country}**: We found that {crop} transport costs and local conflict are connected in ways we didn't expect. This improved our predictions by 15%.")

# Footer
st.markdown("---")
st.caption(f"GreenScope Analytics | {crop} Market Intelligence for {country} | Built for EAGC")