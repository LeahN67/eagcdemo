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

# Enhanced CSS for modern UI
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300   ;400;500;600;700&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    .main {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
    }
    
        .header-container {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        padding: 2.5rem 2rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        box-shadow: 0 10px 40px rgba(15, 23, 42, 0.25);
        border: 1px solid #334155;
    }

    .header-title {
        font-size: 2.8rem;  /* Adjusted for longer title */
        font-weight: 700;
        color: #f8fafc;
        margin: 0;
        letter-spacing: -0.02em;
        line-height: 1.2;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }

    .header-title .brand {
        color: #4ade80;  /* Bright green */
        font-weight: 800;
    }

    .header-subtitle {
        font-size: 1.25rem;
        color: #cbd5e1;
        margin-top: 0.75rem;
        font-weight: 400;
    }    
        .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        border: 1px solid #e2e8f0;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.08);
    }
    
    .metric-label {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #64748b;
        font-weight: 600;
    }
    
    .metric-value {
        font-size: 1.875rem;
        font-weight: 700;
        color: #1e293b;
        margin-top: 0.25rem;
    }
    
    .metric-delta {
        font-size: 0.875rem;
        margin-top: 0.25rem;
    }
    
    .section-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #1e293b;
        margin: 2rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #e2e8f0;
    }
    
    .insight-box {
        background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
        border-left: 4px solid #059669;
        padding: 1.25rem;
        border-radius: 0 12px 12px 0;
        margin: 1rem 0;
    }
    
    .warning-box {
        background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
        border-left: 4px solid #f59e0b;
        padding: 1.25rem;
        border-radius: 0 12px 12px 0;
        margin: 1rem 0;
    }
    
    .scenario-card {
        background: white;
        border: 2px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.25rem;
        text-align: center;
        transition: all 0.2s;
        cursor: pointer;
    }
    
    .scenario-card:hover {
        border-color: #3b82f6;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
    }
    
    .scenario-card.active {
        border-color: #059669;
        background: #f0fdf4;
    }
    
    .stButton>button {
        background: linear-gradient(135deg, #059669 0%, #047857 100%);
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.2s;
    }
    
    .stButton>button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(5, 150, 105, 0.3);
    }
    
    .stSelectbox>div>div, .stSlider>div {
        background: white;
        border-radius: 8px;
    }
    
    div[data-testid="stRadio"] > div {
        background: white;
        padding: 0.5rem;
        border-radius: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
</style>
""", unsafe_allow_html=True)

# CRITICAL FIX: Remove @st.cache_data to ensure fresh data generation
# Or use cache with parameters that change
def create_market_data(crop="Maize", country="Kenya", seed=None, months=36):
    """Generate market data with proper parameter sensitivity"""
    # Use hash of parameters as seed for consistency but change when params change
    if seed is None:
        seed = hash(f"{crop}_{country}_{datetime.now().strftime('%Y%m%d')}") % (2**32)
    np.random.seed(seed)
    
    dates = pd.date_range(start='2022-01-01', periods=months, freq='M')
    
    # Base parameters vary significantly by crop
    crop_params = {
        "Maize": {
            "base_price": 2500, 
            "volatility": 150, 
            "supply_sensitivity": 15,
            "seasonality_amp": 200,
            "color": "#eab308"
        },
        "Beans": {
            "base_price": 4500, 
            "volatility": 350, 
            "supply_sensitivity": 30,
            "seasonality_amp": 400,
            "color": "#8b5cf6"
        },
        "Wheat": {
            "base_price": 3200, 
            "volatility": 180, 
            "supply_sensitivity": 20,
            "seasonality_amp": 250,
            "color": "#06b6d4"
        }
    }
    
    # Country modifiers with meaningful differences
    country_params = {
        "Kenya": {
            "conflict_impact": 1.0, 
            "drought_freq": 0.25,
            "export_disruption": 0.15,
            "transport_premium": 1.0
        },
        "Uganda": {
            "conflict_impact": 0.4, 
            "drought_freq": 0.15,
            "export_disruption": 0.25,
            "transport_premium": 0.85
        },
        "Tanzania": {
            "conflict_impact": 0.3, 
            "drought_freq": 0.12,
            "export_disruption": 0.10,
            "transport_premium": 0.90
        }
    }
    
    params = crop_params.get(crop, crop_params["Maize"])
    c_params = country_params.get(country, country_params["Kenya"])
    
    # Generate market factors with crop/country specific patterns
    t = np.arange(months)
    
    # Seasonality varies by crop
    seasonality = params["seasonality_amp"] * np.sin(2 * np.pi * t / 12 + np.pi/4)
    
    # Harvest cycles
    harvest = 100 + 30 * np.sin(2 * np.pi * t / 12) + np.random.normal(0, 15, months)
    
    # Export disruptions - country specific
    export_stop = np.random.choice([0, 1], size=months, p=[1-c_params["export_disruption"], c_params["export_disruption"]])
    
    # Conflict - country specific
    conflict_base = np.cumsum(np.random.normal(0.01, 0.08, months))
    conflict = np.clip(conflict_base * c_params["conflict_impact"] + 1, 0, 10)
    
    # Drought - country specific
    drought = np.random.choice([0, 1], size=months, p=[1-c_params["drought_freq"], c_params["drought_freq"]])
    
    # Supply calculation with crop-specific sensitivity
    available_supply = (harvest * 0.6 + 
                       (1 - export_stop) * 40 * c_params["transport_premium"] - 
                       conflict * 3 * c_params["conflict_impact"] +
                       np.random.normal(0, 10, months))
    available_supply = np.clip(available_supply, 15, 180)
    
    # Price calculation with full parameter sensitivity
    base_price = params["base_price"] * c_params["transport_premium"]
    
    price = (base_price + seasonality
             - params["supply_sensitivity"] * (available_supply - 80) / 5
             + 80 * export_stop
             + 25 * conflict
             + 300 * drought
             + np.random.normal(0, params["volatility"], months))
    
    # Ensure realistic bounds
    price = np.clip(price, base_price * 0.6, base_price * 2.0)
    
    # Reserves - respond to price spikes
    reserve_stock = np.zeros(months)
    reserve_stock[0] = 500
    for i in range(1, months):
        # Release when price > 130% of base
        release_trigger = price[i] > base_price * 1.3
        release_amount = 60 if release_trigger else 0
        # Replenishment varies by country stability
        replenishment = 25 * (1 - 0.1 * c_params["conflict_impact"])
        reserve_stock[i] = np.clip(reserve_stock[i-1] - release_amount + replenishment, 100, 1200)
    
    # Food security risk - composite index
    price_stress = (price - base_price) / base_price * 50
    supply_stress = np.maximum(0, (80 - available_supply)) * 0.5
    conflict_stress = conflict * 3
    reserve_buffer = np.minimum(0, (reserve_stock - 300) / 10)
    
    food_security_risk = np.clip(20 + price_stress + supply_stress + conflict_stress + reserve_buffer, 0, 100)
    
    return pd.DataFrame({
        'date': dates,
        'harvest': harvest,
        'export_stop': export_stop,
        'conflict': conflict,
        'drought': drought,
        'available_supply': available_supply,
        'market_price': price,
        'reserve_stock': reserve_stock,
        'food_security_risk': food_security_risk,
        'crop': crop,
        'country': country,
        'base_price': base_price
    }), params

# CRITICAL FIX: Scenario-aware data generation - NOW FULLY DYNAMIC WITH months_ahead
def apply_scenario_impact(data, scenario, months_ahead=6):
    """Apply scenario-specific impacts to price projections"""
    last_price = data['market_price'].iloc[-1]
    last_date = data['date'].iloc[-1]
    
    # Scenario impact definitions
    scenario_impacts = {
        "Do nothing (see what happens)": {
            'price_modifier': 1.0,
            'trend': 0.015,  # Slight upward drift
            'volatility': 0.08,
            'description': 'Market continues current trajectory'
        },
        "Release grain reserves": {
            'price_modifier': 0.92,  # 8% reduction
            'trend': 0.005,
            'volatility': 0.05,
            'description': 'Strategic reserve release stabilizes prices'
        },
        "Fix trade routes": {
            'price_modifier': 0.85,  # 15% reduction
            'trend': 0.0,
            'volatility': 0.04,
            'description': 'Improved logistics reduce transport costs'
        },
        "Do both (reserves + routes)": {
            'price_modifier': 0.74,  # 26% reduction
            'trend': -0.005,
            'volatility': 0.03,
            'description': 'Combined intervention maximizes impact'
        }
    }
    
    impact = scenario_impacts.get(scenario, scenario_impacts["Do nothing (see what happens)"])
    
    # Generate future dates - DYNAMIC based on months_ahead
    future_dates = pd.date_range(start=last_date + pd.DateOffset(months=1), periods=months_ahead, freq='M')
    
    # Generate scenario-specific price path - DYNAMIC length based on months_ahead
    np.random.seed(hash(f"{scenario}_{months_ahead}") % 2**32)  # Seed includes months_ahead for reproducibility
    prices = []
    current_price = last_price * impact['price_modifier']
    
    for i in range(months_ahead):
        # Mean reversion toward base
        base = data['base_price'].iloc[0]
        reversion = 0.1 * (base - current_price) / base
        trend = impact['trend']
        shock = np.random.normal(0, impact['volatility'])
        
        current_price = current_price * (1 + reversion + trend + shock)
        prices.append(current_price)
    
    return future_dates, np.array(prices), impact

def get_scenario_metrics(crop, country, scenario):
    """Calculate metrics with crop and country sensitivity"""
    # Base metrics by crop
    crop_base = {
        "Maize": {"price": 2800, "intervention_cost": 1.0},
        "Beans": {"price": 4800, "intervention_cost": 1.3},
        "Wheat": {"price": 3400, "intervention_cost": 1.1}
    }
    
    # Country cost adjustments
    country_factor = {
        "Kenya": 1.0,
        "Uganda": 0.85,
        "Tanzania": 0.90
    }
    
    base = crop_base.get(crop, crop_base["Maize"])
    factor = country_factor.get(country, 1.0)
    
    # Scenario definitions with crop-specific impacts
    scenarios = {
        "Do nothing (see what happens)": {
            'price_drop': 0, 
            'cost': 0, 
            'confidence': 95,
            'people_helped': 0,
            'timeline': '-',
            'description': f'{crop} prices follow market forces in {country}'
        },
        "Release grain reserves": {
            'price_drop': 8 if crop == "Maize" else 10 if crop == "Wheat" else 12, 
            'cost': int(150 * factor * base["intervention_cost"]), 
            'confidence': 85,
            'people_helped': round(1.2 * factor, 1),
            'timeline': '2-3 weeks',
            'description': f'Strategic {crop.lower()} reserve release to stabilize {country} market'
        },
        "Fix trade routes": {
            'price_drop': 15 if crop == "Maize" else 18 if crop == "Wheat" else 20, 
            'cost': int(80 * factor * base["intervention_cost"]), 
            'confidence': 82,
            'people_helped': round(1.8 * factor, 1),
            'timeline': '4-6 weeks',
            'description': f'Infrastructure investment to improve {crop.lower()} transport in {country}'
        },
        "Do both (reserves + routes)": {
            'price_drop': 26 if crop == "Maize" else 30 if crop == "Wheat" else 35, 
            'cost': int(200 * factor * base["intervention_cost"]), 
            'confidence': 78,
            'people_helped': round(2.5 * factor, 1),
            'timeline': '6-8 weeks',
            'description': f'Comprehensive {crop.lower()} market intervention in {country}'
        }
    }
    
    return scenarios.get(scenario, scenarios["Do nothing (see what happens)"])

# Header
st.markdown("""
<div class="header-container">
    <h1 class="header-title"><span class="brand">🌾 GreenScope</span> Analytics Data Infrastructure</h1>
    <p class="header-subtitle">Market Intelligence for Smarter Agricultural Decisions</p>
</div>
""", unsafe_allow_html=True)

# Sidebar with improved styling
with st.sidebar:
    st.markdown("### 🎯 Configuration")
    
    st.markdown("**Market Selection**")
    country = st.selectbox(
        "Country", 
        ["Kenya", "Uganda", "Tanzania"],
        help="Select focus country for market analysis"
    )
    
    crop = st.selectbox(
        "Crop", 
        ["Maize", "Beans", "Wheat"],
        help="Select commodity for price analysis"
    )
    
    st.markdown("---")
    st.markdown("**Scenario Testing**")
    
    scenario = st.selectbox(
        "Test Intervention Scenario",
        [
            "Do nothing (see what happens)",
            "Release grain reserves",
            "Fix trade routes",
            "Do both (reserves + routes)"
        ],
        help="See how different actions affect future prices"
    )
    
    # DYNAMIC FORECAST MONTHS SLIDER
    months_ahead = st.slider(
        "Forecast Months", 
        min_value=3, 
        max_value=12, 
        value=6,
        step=1,
        help="How far ahead to project (3-12 months)"
    )
    
    # Show current selection
    st.markdown(f"""
    <div style="background: #eff6ff; border-radius: 6px; padding: 8px; margin-top: 8px; border: 1px solid #bfdbfe;">
        <div style="font-size: 0.75rem; color: #1e40af; font-weight: 600;">FORECAST PERIOD</div>
        <div style="font-size: 1rem; color: #1e2937; font-weight: 700;">{months_ahead} months</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Live indicator
    st.markdown(f"""
    <div style="background: #f0fdf4; border-radius: 8px; padding: 12px; border: 1px solid #86efac;">
        <div style="font-size: 0.75rem; color: #166534; font-weight: 600;">ACTIVE CONFIGURATION</div>
        <div style="font-size: 0.875rem; color: #1f2937; margin-top: 4px;">
            📍 {country}<br>
            🌾 {crop}<br>
            📊 {scenario}<br>
            📅 {months_ahead} month forecast
        </div>
    </div>
    """, unsafe_allow_html=True)

# Generate data with current parameters
data, crop_params = create_market_data(crop=crop, country=country)
current_metrics = get_scenario_metrics(crop, country, scenario)

# Navigation
st.markdown("---")
report_choice = st.radio(
    "Select Analysis View",
    ["📊 Market Overview", "🔍 Price Drivers", "💡 Scenario Comparison", "📈 Performance Tracking"],
    horizontal=True,
    label_visibility="collapsed"
)

# COLOR THEME based on crop
crop_colors = {
    "Maize": {"primary": "#eab308", "secondary": "#fef08a", "accent": "#a16207"},
    "Beans": {"primary": "#8b5cf6", "secondary": "#ddd6fe", "accent": "#6d28d9"},
    "Wheat": {"primary": "#06b6d4", "secondary": "#cffafe", "accent": "#0891b2"}
}
theme = crop_colors.get(crop, crop_colors["Maize"])

# VIEW 1: Market Overview
if "Market Overview" in report_choice:
    st.markdown('<div class="section-header">Market Overview</div>', unsafe_allow_html=True)
    
    # Key metrics with crop-specific context
    cols = st.columns(4)
    
    current_price = data['market_price'].iloc[-1]
    price_6m_ago = data['market_price'].iloc[-6]
    price_change = ((current_price / price_6m_ago) - 1) * 100
    
    with cols[0]:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Current {crop} Price</div>
            <div class="metric-value" style="color: {theme['primary']}">KES {current_price:,.0f}</div>
            <div class="metric-delta" style="color: {'#ef4444' if price_change > 10 else '#22c55e' if price_change < -5 else '#64748b'}">
                {price_change:+.1f}% vs 6mo ago
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with cols[1]:
        supply_status = "Tight" if data['available_supply'].iloc[-1] < 50 else "Moderate" if data['available_supply'].iloc[-1] < 90 else "Adequate"
        supply_color = "#ef4444" if supply_status == "Tight" else "#f59e0b" if supply_status == "Moderate" else "#22c55e"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Supply Status</div>
            <div class="metric-value" style="color: {supply_color}">{supply_status}</div>
            <div class="metric-delta" style="color: #64748b">{data['available_supply'].iloc[-1]:.0f}% of normal</div>
        </div>
        """, unsafe_allow_html=True)
    
    with cols[2]:
        risk = data['food_security_risk'].iloc[-1]
        risk_level = "High" if risk > 60 else "Elevated" if risk > 40 else "Moderate" if risk > 25 else "Low"
        risk_color = "#dc2626" if risk > 60 else "#ea580c" if risk > 40 else "#ca8a04" if risk > 25 else "#16a34a"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Food Security Risk</div>
            <div class="metric-value" style="color: {risk_color}">{risk_level}</div>
            <div class="metric-delta" style="color: #64748b">Score: {risk:.0f}/100</div>
        </div>
        """, unsafe_allow_html=True)
    
    with cols[3]:
        reserves = data['reserve_stock'].iloc[-1]
        reserve_months = reserves / 50  # Assuming 50k MT monthly need
        reserve_color = "#dc2626" if reserve_months < 3 else "#ea580c" if reserve_months < 6 else "#16a34a"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Strategic Reserves</div>
            <div class="metric-value" style="color: {reserve_color}">{reserves:.0f}k MT</div>
            <div class="metric-delta" style="color: #64748b">~{reserve_months:.1f} months coverage</div>
        </div>
        """, unsafe_allow_html=True)
    
    # NEW: Dynamic Scenario Impact Section - Shows metrics for selected scenario
    if scenario != "Do nothing (see what happens)":
        st.markdown(f'<div class="section-header">Selected Scenario Impact ({months_ahead}-Month Forecast)</div>', unsafe_allow_html=True)
        
        # Calculate dynamic price reduction based on projection - USING DYNAMIC months_ahead
        future_dates, future_prices, impact = apply_scenario_impact(data, scenario, months_ahead)
        price_reduction = (1 - future_prices[0] / data['market_price'].iloc[-1]) * 100
        
        # Calculate end-of-period metrics
        end_price = future_prices[-1]
        total_change = ((end_price / current_price) - 1) * 100
        
        scen_cols = st.columns(4)
        
        with scen_cols[0]:
            st.markdown(f"""
            <div class="metric-card" style="border-left: 4px solid #059669;">
                <div class="metric-label">Expected Price Drop</div>
                <div class="metric-value" style="color: #059669;">{price_reduction:.1f}%</div>
                <div class="metric-delta" style="color: #64748b;">First month impact</div>
            </div>
            """, unsafe_allow_html=True)
        
        with scen_cols[1]:
            st.markdown(f"""
            <div class="metric-card" style="border-left: 4px solid #3b82f6;">
                <div class="metric-label">Implementation Cost</div>
                <div class="metric-value" style="color: #1e293b;">KES {current_metrics['cost']}M</div>
                <div class="metric-delta" style="color: #64748b;">{country}-specific estimate</div>
            </div>
            """, unsafe_allow_html=True)
        
        with scen_cols[2]:
            st.markdown(f"""
            <div class="metric-card" style="border-left: 4px solid #8b5cf6;">
                <div class="metric-label">People Protected</div>
                <div class="metric-value" style="color: #1e293b;">{current_metrics['people_helped']}M</div>
                <div class="metric-delta" style="color: #64748b;">Over {months_ahead} months</div>
            </div>
            """, unsafe_allow_html=True)
        
        with scen_cols[3]:
            conf_color = "#16a34a" if current_metrics['confidence'] >= 85 else "#f59e0b" if current_metrics['confidence'] >= 75 else "#ef4444"
            st.markdown(f"""
            <div class="metric-card" style="border-left: 4px solid {conf_color};">
                <div class="metric-label">Confidence Level</div>
                <div class="metric-value" style="color: {conf_color};">{current_metrics['confidence']}%</div>
                <div class="metric-delta" style="color: #64748b;">Model certainty</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Scenario description and timeline - DYNAMIC based on months_ahead
        st.markdown(f"""
        <div class="insight-box">
            <strong>Active Scenario: {scenario}</strong> ({months_ahead}-month projection)<br>
            {current_metrics['description']}<br>
            <strong>Timeline:</strong> {current_metrics['timeline']} | 
            <strong>Projected price path:</strong> KES {future_prices[0]:,.0f} (Month 1) → KES {end_price:,.0f} (Month {months_ahead}) | 
            <strong>Total change:</strong> {total_change:+.1f}%
        </div>
        """, unsafe_allow_html=True)
    
    # Alerts section
    alerts = []
    if price_change > 15:
        alerts.append(("Price Spike", f"{crop} prices up {price_change:.1f}% in 6 months", "warning"))
    if risk > 55:
        alerts.append(("Food Security", "Risk elevated—intervention may be needed", "alert"))
    if reserve_months < 4:
        alerts.append(("Low Reserves", "Strategic buffer below comfort level", "warning"))
    if data['export_stop'].iloc[-3:].mean() > 0.4:
        alerts.append(("Trade Disruption", "Export restrictions affecting supply", "warning"))
    
    # Add scenario-specific alerts
    if scenario != "Do nothing (see what happens)" and current_metrics['confidence'] < 80:
        alerts.append(("Confidence Warning", f"{scenario} has {current_metrics['confidence']}% confidence—consider additional data", "warning"))
    
    if alerts:
        st.markdown('<div class="section-header">Active Alerts</div>', unsafe_allow_html=True)
        for title, message, level in alerts[:3]:
            if level == "alert":
                st.error(f"**{title}:** {message}")
            else:
                st.warning(f"**{title}:** {message}")
    else:
        st.success("✓ All market indicators within normal parameters")
    
    # Price chart with scenario overlay - DYNAMIC months_ahead
    st.markdown(f'<div class="section-header">Price Trajectory & {months_ahead}-Month Scenario Impact</div>', unsafe_allow_html=True)
    
    fig, ax = plt.subplots(figsize=(12, 5))
    
    # Historical data
    ax.plot(data['date'], data['market_price'], 
            linewidth=2.5, color=theme['primary'], 
            label=f'Historical {crop} Price', alpha=0.9)
    
    # Add trend line
    z = np.polyfit(range(len(data)), data['market_price'], 1)
    p = np.poly1d(z)
    ax.plot(data['date'], p(range(len(data))), 
            "--", color=theme['accent'], linewidth=1.5, alpha=0.6, label='Trend')
    
    # Scenario projection - DYNAMIC months_ahead
    future_dates, future_prices, impact = apply_scenario_impact(data, scenario, months_ahead)
    
    # Dynamic color based on scenario
    if 'both' in scenario:
        line_color = '#059669'  # Green for combined
    elif scenario == "Do nothing (see what happens)":
        line_color = '#ef4444'  # Red for do nothing
    else:
        line_color = '#3b82f6'  # Blue for single interventions
    
    ax.plot(future_dates, future_prices, 
            linewidth=3, color=line_color,
            linestyle='--', marker='o', markersize=6,
            label=f'{scenario} ({months_ahead} mo)')
    
    # Reference lines
    base_price = data['base_price'].iloc[0]
    ax.axhline(y=base_price * 1.3, color='#dc2626', linestyle=':', alpha=0.7, label='Crisis threshold')
    ax.axhline(y=base_price, color='#64748b', linestyle=':', alpha=0.5, label='Long-term average')
    
    # Fill zones
    ax.fill_between(data['date'], data['market_price'].min() * 0.8, base_price * 1.3, 
                    alpha=0.05, color='#22c55e')
    
    ax.set_ylabel(f'Price (KES per 90kg {crop.lower()} bag)', fontsize=11)
    ax.set_xlabel('Date', fontsize=11)
    ax.legend(loc='best', framealpha=0.95)
    ax.grid(True, alpha=0.3, linestyle='-')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    st.pyplot(fig)
    
    # Scenario comparison mini-table - DYNAMIC
    if scenario != "Do nothing (see what happens)":
        # Get metrics for all scenarios for comparison
        all_metrics = {
            "Do nothing": get_scenario_metrics(crop, country, "Do nothing (see what happens)"),
            "Selected": current_metrics
        }
        
        st.markdown(f"""
        <div style="background: #f8fafc; border-radius: 8px; padding: 12px; margin-top: 1rem;">
            <strong>Scenario Comparison for {crop} in {country} ({months_ahead}-month horizon)</strong><br>
            <table style="width: 100%; font-size: 0.875rem; margin-top: 8px;">
                <tr style="border-bottom: 1px solid #e2e8f0;">
                    <td style="padding: 8px 0;"><strong>Do Nothing</strong></td>
                    <td style="padding: 8px 0; text-align: right;">0% price drop</td>
                    <td style="padding: 8px 0; text-align: right;">KES 0M cost</td>
                    <td style="padding: 8px 0; text-align: right;">0M helped</td>
                </tr>
                <tr style="background: #f0fdf4; border-left: 3px solid #059669;">
                    <td style="padding: 8px 0;"><strong>{scenario}</strong> (Selected)</td>
                    <td style="padding: 8px 0; text-align: right; color: #059669; font-weight: 600;">{current_metrics['price_drop']}% drop</td>
                    <td style="padding: 8px 0; text-align: right;">KES {current_metrics['cost']}M</td>
                    <td style="padding: 8px 0; text-align: right;">{current_metrics['people_helped']}M helped</td>
                </tr>
            </table>
        </div>
        """, unsafe_allow_html=True)

# VIEW 2: Price Drivers
elif "Price Drivers" in report_choice:
    st.markdown(f'<div class="section-header">What&apos;s Driving {crop} Prices in {country}?</div>', unsafe_allow_html=True)
    
    # Show current forecast setting
    st.info(f"📅 Current forecast setting: **{months_ahead} months** (adjust in sidebar)")
    
    # Dynamic causal factors based on data
    factors = []
    
    # Calculate actual contributions from data
    export_impact = data['export_stop'].iloc[-6:].mean() * 35
    drought_impact = data['drought'].iloc[-6:].mean() * 25
    conflict_impact = min(data['conflict'].iloc[-1] / 10 * 20, 25)
    supply_gap = max(0, (80 - data['available_supply'].iloc[-1]) / 80 * 20)
    
    if export_impact > 10:
        factors.append(("Export Restrictions", f"Regional trade barriers affecting {crop.lower()} flows", export_impact, "#dc2626"))
    if drought_impact > 5:
        factors.append(("Weather Stress", "Below-normal rainfall reducing yield expectations", drought_impact, "#ea580c"))
    if conflict_impact > 8:
        factors.append(("Logistics Disruption", "Transport corridor instability increasing costs", conflict_impact, "#ca8a04"))
    if supply_gap > 10:
        factors.append(("Supply Shortfall", "Low stock levels relative to demand", supply_gap, "#eab308"))
    
    if not factors:
        factors.append(("Stable Conditions", "Standard seasonal patterns, no major disruptions", 5, "#16a34a"))
    
    # Display factors
    cols = st.columns(len(factors))
    for i, (col, (name, desc, impact, color)) in enumerate(zip(cols, factors)):
        with col:
            st.markdown(f"""
            <div style="background: white; border-radius: 12px; padding: 1.25rem; border-top: 4px solid {color}; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">{['🚫','🌤️','⚠️','📉','✓'][i]}</div>
                <div style="font-weight: 600; color: #1f2937; margin-bottom: 0.25rem;">{name}</div>
                <div style="font-size: 0.875rem; color: #64748b; margin-bottom: 0.5rem;">{desc}</div>
                <div style="font-size: 1.25rem; font-weight: 700; color: {color};">{impact:.0f}%</div>
                <div style="font-size: 0.75rem; color: #9ca3af;">estimated impact</div>
            </div>
            """, unsafe_allow_html=True)
    
    # Causal diagram
    st.markdown('<div class="section-header">How Factors Connect</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        fig, ax = plt.subplots(figsize=(10, 7))
        G = nx.DiGraph()
        
        # Dynamic edges based on active factors
        edges = [
            ("Weather", "Crop Yield", 0.7),
            ("Trade Policy", "Market Access", 0.8),
            ("Conflict", "Transport Cost", 0.6),
            ("Crop Yield", f"{crop} Supply", 0.9),
            ("Market Access", f"{crop} Supply", 0.85),
            ("Transport Cost", f"{crop} Price", 0.5),
            (f"{crop} Supply", f"{crop} Price", 0.95),
            (f"{crop} Price", "Food Security", 0.75)
        ]
        
        for source, target, strength in edges:
            G.add_edge(source, target, weight=strength)
        
        pos = nx.spring_layout(G, seed=42, k=2.5)
        
        # Draw nodes with crop-specific color
        node_colors = [theme['primary'] if crop in node or 'Supply' in node or 'Price' in node else '#64748b' 
                       for node in G.nodes()]
        
        nx.draw_networkx_nodes(G, pos, node_color=node_colors, 
                              node_size=3500, alpha=0.9, ax=ax)
        nx.draw_networkx_labels(G, pos, font_size=9, font_color='white',
                               font_weight='bold', ax=ax)
        
        # Draw edges with varying thickness
        edge_weights = [d['weight']*4 for (u, v, d) in G.edges(data=True)]
        nx.draw_networkx_edges(G, pos, width=edge_weights, 
                              edge_color='#475569', alpha=0.6,
                              arrows=True, arrowsize=20, ax=ax)
        
        ax.set_title(f"Causal Pathways: {crop} Market in {country}", 
                    fontsize=12, fontweight='bold', pad=20)
        ax.axis('off')
        st.pyplot(fig)
    
    with col2:
        st.markdown("""
        <div style="background: #f8fafc; border-radius: 12px; padding: 1.25rem;">
            <div style="font-weight: 600; color: #1f2937; margin-bottom: 0.75rem;">How to Read</div>
            <div style="font-size: 0.875rem; color: #64748b; line-height: 1.6;">
                • <strong>Nodes</strong> = Market factors<br>
                • <strong>Arrows</strong> = Causal influence<br>
                • <strong>Thickness</strong> = Strength of effect<br><br>
                <strong style="color: """ + theme['primary'] + """;">Colored nodes</strong> show 
                your selected crop's specific pathway through the market system.
            </div>
        </div>
        """, unsafe_allow_html=True)

# VIEW 3: Scenario Comparison
elif "Scenario Comparison" in report_choice:
    st.markdown(f'<div class="section-header">Compare Intervention Scenarios for {crop}</div>', unsafe_allow_html=True)
    
    # Show current forecast setting prominently
    st.markdown(f"""
    <div style="background: #eff6ff; border-radius: 8px; padding: 12px; margin-bottom: 1rem; border: 1px solid #bfdbfe;">
        <div style="font-size: 0.875rem; color: #1e40af;">
            <strong>Forecast Horizon:</strong> {months_ahead} months | 
            <strong>Country:</strong> {country} | 
            <strong>Crop:</strong> {crop}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Get all scenarios for this crop/country - DYNAMICALLY CALCULATED
    all_scenarios = {
        'Current Trajectory': get_scenario_metrics(crop, country, "Do nothing (see what happens)"),
        'Release Reserves': get_scenario_metrics(crop, country, "Release grain reserves"),
        'Improve Routes': get_scenario_metrics(crop, country, "Fix trade routes"),
        'Combined Approach': get_scenario_metrics(crop, country, "Do both (reserves + routes)")
    }
    
    # Scenario cards
    st.markdown("**Select to compare:**")
    cols = st.columns(4)
    
    for i, (col, (name, metrics)) in enumerate(zip(cols, all_scenarios.items())):
        is_active = name.replace('Current Trajectory', 'Do nothing').replace('Release Reserves', 'Release grain').replace('Improve Routes', 'Fix trade').replace('Combined Approach', 'Do both') in scenario
        
        with col:
            impact_color = '#ef4444' if metrics['price_drop'] == 0 else '#22c55e'
            st.markdown(f"""
            <div class="scenario-card {'active' if is_active else ''}" style="border-color: {impact_color if is_active else '#e2e8f0'};">
                <div style="font-size: 0.875rem; font-weight: 600; color: #374151; margin-bottom: 0.5rem;">{name}</div>
                <div style="font-size: 2rem; font-weight: 700; color: {impact_color};">{metrics['price_drop']}%</div>
                <div style="font-size: 0.75rem; color: #6b7280; margin-bottom: 0.75rem;">price impact</div>
                <div style="font-size: 0.875rem; color: #374151;"><strong>KES {metrics['cost']}M</strong></div>
                <div style="font-size: 0.75rem; color: #6b7280;">{metrics['people_helped']}M people helped</div>
                <div style="font-size: 0.75rem; color: #6b7280; margin-top: 0.5rem;">{metrics['confidence']}% confidence</div>
            </div>
            """, unsafe_allow_html=True)
    
    # Comparison chart - DYNAMIC months_ahead
    st.markdown(f'<div class="section-header">Projected Price Paths ({months_ahead} Months)</div>', unsafe_allow_html=True)
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # DYNAMIC month labels based on months_ahead
    month_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][:months_ahead]
    
    for i, (name, scen_metrics) in enumerate(all_scenarios.items()):
        future_dates, prices, impact = apply_scenario_impact(
            data, 
            name.replace('Current Trajectory', 'Do nothing (see what happens)')
                .replace('Release Reserves', 'Release grain reserves')
                .replace('Improve Routes', 'Fix trade routes')
                .replace('Combined Approach', 'Do both (reserves + routes)'),
            months_ahead  # DYNAMIC
        )
        
        color = ['#ef4444', '#f59e0b', '#3b82f6', '#059669'][i]
        linewidth = 3 if name.replace('Current Trajectory', 'Do nothing').replace('Release Reserves', 'Release grain').replace('Improve Routes', 'Fix trade').replace('Combined Approach', 'Do both') in scenario else 2
        alpha = 1.0 if name.replace('Current Trajectory', 'Do nothing').replace('Release Reserves', 'Release grain').replace('Improve Routes', 'Fix trade').replace('Combined Approach', 'Do both') in scenario else 0.6
        
        ax.plot(future_dates, prices, 
                linewidth=linewidth, color=color, alpha=alpha,
                marker='o', markersize=6 if linewidth == 3 else 4,
                label=f"{name} ({scen_metrics['price_drop']}%)")
    
    ax.axhline(y=data['base_price'].iloc[0] * 1.3, color='#dc2626', linestyle='--', alpha=0.5, label='Crisis level')
    
    ax.set_ylabel(f'Projected Price (KES/{crop.lower()})', fontsize=11)
    ax.set_xlabel(f'Months Ahead ({months_ahead}-month horizon)', fontsize=11)
    ax.legend(loc='best', framealpha=0.95)
    ax.grid(True, alpha=0.3)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    st.pyplot(fig)
    
    # Selected scenario details - DYNAMICALLY UPDATED
    st.markdown(f'<div class="section-header">Your Selected Scenario ({months_ahead}-Month Horizon)</div>', unsafe_allow_html=True)
    
    cols = st.columns(3)
    with cols[0]:
        st.metric("Expected Price Reduction", f"{current_metrics['price_drop']}%")
    with cols[1]:
        st.metric("Implementation Cost", f"KES {current_metrics['cost']}M")
    with cols[2]:
        st.metric("People Protected", f"{current_metrics['people_helped']}M")
    
    st.info(f"**{scenario}** ({months_ahead}-month forecast): {current_metrics['description']}")

# VIEW 4: Performance Tracking
else:
    st.markdown('<div class="section-header">Platform Performance & Accuracy</div>', unsafe_allow_html=True)
    
    # Show current forecast setting
    st.info(f"📅 Current forecast setting: **{months_ahead} months** | Model performance tracked across all forecast horizons")
    
    # Model performance for this crop/country
    st.markdown(f"**Tracking {crop} model accuracy in {country}**")
    
    # Simulate improving accuracy over time
    np.random.seed(hash(f"{crop}_{country}") % 2**32)
    history = pd.DataFrame({
        'Prediction #': range(1, 9),
        'Error (%)': [18, 14, 15, 11, 9, 10, 8, 7],
        'Confidence': [68, 72, 75, 80, 83, 85, 87, 89]
    })
    
    fig, ax1 = plt.subplots(figsize=(12, 5))
    
    color1 = '#ef4444'
    ax1.set_xlabel('Prediction Number', fontsize=11)
    ax1.set_ylabel('Prediction Error (%)', color=color1, fontsize=11)
    ax1.plot(history['Prediction #'], history['Error (%)'], 
            color=color1, marker='o', linewidth=2.5, markersize=8, label='Error rate')
    ax1.fill_between(history['Prediction #'], history['Error (%)'], alpha=0.2, color=color1)
    ax1.tick_params(axis='y', labelcolor=color1)
    
    ax2 = ax1.twinx()
    color2 = '#059669'
    ax2.set_ylabel('Model Confidence (%)', color=color2, fontsize=11)
    ax2.plot(history['Prediction #'], history['Confidence'], 
            color=color2, marker='s', linewidth=2.5, markersize=8, linestyle='--', label='Confidence')
    ax2.tick_params(axis='y', labelcolor=color2)
    ax2.set_ylim(60, 95)
    
    # Trend annotation
    ax1.annotate('Learning from\ninterventions', 
                xy=(6, 8), xytext=(4.5, 12),
                arrowprops=dict(arrowstyle='->', color='#64748b'),
                fontsize=9, color='#64748b', ha='center')
    
    fig.tight_layout()
    st.pyplot(fig)
    
    # Current stats
    cols = st.columns(4)
    with cols[0]:
        st.metric("Current Error Rate", "7.2%", "-10.8pp from start")
    with cols[1]:
        st.metric("Model Confidence", "89%", "+21pp improvement")
    with cols[2]:
        st.metric("Predictions Made", "24", f"This quarter ({months_ahead}mo horizon)")
    with cols[3]:
        st.metric("Validation Status", "✓ Active", "Real-time monitoring")
    
    # Learning insights
    st.markdown('<div class="section-header">Key Learnings for {0} in {1}</div>'.format(crop, country), unsafe_allow_html=True)
    
    learnings = {
        "Maize": "Transport cost sensitivity is 2x higher than initially modeled. Conflict in key corridors has non-linear price effects.",
        "Beans": "Export ban announcements create anticipatory price spikes 2-3 weeks before implementation. Early warning critical.",
        "Wheat": "Climate correlation strongest in Rift Valley region. Satellite vegetation indices improve forecast accuracy by 15%."
    }
    
    st.success(f"💡 **Insight:** {learnings.get(crop, 'Continuous model refinement improving accuracy.')}")

# Footer - DYNAMIC months_ahead display
st.markdown("---")
st.markdown(f"""
<div style="display: flex; justify-content: space-between; align-items: center; padding: 1rem 0; color: #64748b; font-size: 0.875rem;">
    <div>
        <strong>GreenScope Analytics</strong> | Market Intelligence Infrastructure
    </div>
    <div>
        {crop} • {country} • {scenario} • {months_ahead}mo forecast | v2.1.0
    </div>
</div>
""", unsafe_allow_html=True)