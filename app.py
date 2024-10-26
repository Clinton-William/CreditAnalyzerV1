# Import necessary libraries
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import math
from scipy.stats import norm
from login_system import initialize_login_system
from typing import List, Dict, Tuple, Optional
import requests

# Set page configuration - only once at the start
st.set_page_config(
    page_title="Financial Health Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)
# Define CSS styles - consolidated and organized
st.markdown("""
<style>
    /* Global Styles */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    /* Main Container */
    .main {
        background-color: #0e1117;
        color: #ffffff;
    }
    
    /* Cards and Containers */
    .metric-card {
        background: linear-gradient(135deg, #1f2937 0%, #111827 100%);
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid rgba(255,255,255,0.1);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        margin: 10px 0;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 20px rgba(0,0,0,0.2);
    }
    
    .company-header {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        padding: 2rem;
        border-radius: 16px;
        margin: 1.5rem 0;
        border: 1px solid rgba(255,255,255,0.1);
        box-shadow: 0 8px 16px rgba(0,0,0,0.1);
    }
    
    .search-container {
        background: linear-gradient(135deg, rgba(37,38,43,0.7) 0%, rgba(37,38,43,0.5) 100%);
        backdrop-filter: blur(10px);
        padding: 2rem;
        border-radius: 16px;
        margin: 1rem 0;
        border: 1px solid rgba(255,255,255,0.1);
    }
    
    /* Text Styles */
    .metric-label {
        color: #94a3b8;
        font-size: 1rem;
        margin-bottom: 8px;
    }
    
    .metric-value {
        color: #FFF5E1;
        font-size: 1.8rem;
        font-weight: bold;
        margin: 0;
    }
    
    h1 {
        font-size: 2.5rem !important;
        font-weight: 700 !important;
        margin-bottom: 1rem !important;
        color: #ffffff !important;
    }
    
    h2 {
        font-size: 1.8rem !important;
        font-weight: 600 !important;
        color: #ffffff !important;
    }
    
    h3 {
        font-size: 1.5rem !important;
        font-weight: 600 !important;
        color: #ffffff !important;
    }
    
    /* Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: white;
        padding: 0.75rem 2rem;
        border-radius: 8px;
        border: none;
        font-weight: 600;
        transition: all 0.3s ease;
        width: 100%;
        max-width: 300px;
    }
    
    .stButton>button:hover {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
        transform: translateY(-2px);
        box-shadow: 0 8px 16px rgba(0,0,0,0.2);
    }
    
    /* Alerts */
    .data-warning {
        background: rgba(251, 191, 36, 0.1);
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #fbbf24;
        margin: 1rem 0;
    }
    
    .data-info {
        background: rgba(59, 130, 246, 0.1);
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #3b82f6;
        margin: 1rem 0;
    }
    
    /* Score Badges */
    .score-badge {
        padding: 0.5rem 1rem;
        border-radius: 6px;
        font-weight: 600;
        display: inline-block;
        margin-top: 0.5rem;
    }
    
    .safe-zone {
        background: rgba(34, 197, 94, 0.2);
        color: #22c55e;
        border: 1px solid rgba(34, 197, 94, 0.3);
    }
    
    .grey-zone {
        background: rgba(234, 179, 8, 0.2);
        color: #eab308;
        border: 1px solid rgba(234, 179, 8, 0.3);
    }
    
    .distress-zone {
        background: rgba(239, 68, 68, 0.2);
        color: #ef4444;
        border: 1px solid rgba(239, 68, 68, 0.3);
    }
    
    /* Input Fields */
    .stTextInput > div > div {
        background-color: #1f2937 !important;
        border-radius: 8px !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        padding: 0.5rem 1rem !important;
    }
    
    .stTextInput > div > div:focus-within {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2) !important;
    }
    
    /* Metrics Display */
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: 700 !important;
        color: #ffffff !important;
    }
    
    div[data-testid="stMetricLabel"] {
        font-size: 1rem !important;
        font-weight: 500 !important;
        color: #9ca3af !important;
    }
</style>
""", unsafe_allow_html=True)

# Helper Functions for Data Processing

def is_problematic(value):
    """Check if a value is problematic (nan, inf, 0, or very small)"""
    try:
        return (pd.isna(value) or 
                np.isinf(value) or 
                value == 0 or 
                abs(float(value)) < 1e-6)
    except:
        return True

def safe_get(df, keys, index=0):
    """
    Safely get value from dataframe with multiple possible keys
    Args:
        df: pandas DataFrame
        keys: list of possible column names
        index: which row to get (default 0 for most recent)
    Returns:
        value, key_used (or default value, None if not found)
    """
    try:
        for key in keys:
            if key in df.index:
                value = df.loc[key].iloc[index]
                if not is_problematic(value):
                    return value, key
        return 0, None
    except Exception as e:
        print(f"Error in safe_get: {str(e)}")
        return 0, None

def get_merton_color(prob):
    """Get background color based on Merton probability"""
    if prob < 0.05:  # Very low risk
        return "rgba(76, 175, 80, 0.2)"
    elif prob < 0.15:  # Low risk
        return "rgba(255, 193, 7, 0.2)"
    else:  # High risk
        return "rgba(255, 82, 82, 0.2)"

# Replace the existing create_dual_gauge_chart function with this:
def create_gauge_charts(z_score, o_prob, merton_prob):
    """Create a three-gauge chart showing Z-Score, O-Score, and Merton probabilities"""
    # Calculate dynamic max range for Z-score
    max_range_z = max(5, math.ceil(z_score if z_score is not None else 5 + 0.5))
    
    # Create figure with three indicators
    fig = make_subplots(
        rows=1, cols=3,
        specs=[[{"type": "indicator"}, {"type": "indicator"}, {"type": "indicator"}]]
    )
    
    # Add Z-score gauge if available
    if z_score is not None:
        fig.add_trace(
            go.Indicator(
                mode="gauge+number",
                value=z_score,
                title={'text': "Altman Z-Score", 'font': {'size': 24, 'color': '#FFF5E1'}},
                gauge={
                    'axis': {
                        'range': [0, max_range_z],
                        'tickwidth': 1,
                        'tickcolor': "#FFF5E1",
                        'tickfont': {'color': '#FFF5E1'}
                    },
                    'bar': {'color': "#1e3c72"},
                    'bgcolor': "rgba(0,0,0,0)",
                    'borderwidth': 2,
                    'bordercolor': "gray",
                    'steps': [
                        {'range': [0, 1.81], 'color': 'rgba(255, 82, 82, 0.3)'},
                        {'range': [1.81, 2.99], 'color': 'rgba(255, 193, 7, 0.3)'},
                        {'range': [2.99, max_range_z], 'color': 'rgba(76, 175, 80, 0.3)'}
                    ]
                }
            ),
            row=1, col=1
        )
    
    # Add O-score gauge if available
    if o_prob is not None:
        fig.add_trace(
            go.Indicator(
                mode="gauge+number",
                value=o_prob * 100,  # Convert to percentage
                title={'text': "Ohlson Probability", 'font': {'size': 24, 'color': '#FFF5E1'}},
                number={'suffix': '%', 'font': {'color': '#FFF5E1'}},
                gauge={
                    'axis': {
                        'range': [0, 100],
                        'tickwidth': 1,
                        'tickcolor': "#FFF5E1",
                        'tickfont': {'color': '#FFF5E1'}
                    },
                    'bar': {'color': "#1e3c72"},
                    'bgcolor': "rgba(0,0,0,0)",
                    'borderwidth': 2,
                    'bordercolor': "gray",
                    'steps': [
                        {'range': [0, 30], 'color': 'rgba(76, 175, 80, 0.3)'},
                        {'range': [30, 70], 'color': 'rgba(255, 193, 7, 0.3)'},
                        {'range': [70, 100], 'color': 'rgba(255, 82, 82, 0.3)'}
                    ]
                }
            ),
            row=1, col=2
        )

    # Add Merton gauge if available
    if merton_prob is not None:
        fig.add_trace(
            go.Indicator(
                mode="gauge+number",
                value=merton_prob * 100,  # Convert to percentage
                title={'text': "Merton Probability", 'font': {'size': 24, 'color': '#FFF5E1'}},
                number={'suffix': '%', 'font': {'color': '#FFF5E1'}},
                gauge={
                    'axis': {
                        'range': [0, 100],
                        'tickwidth': 1,
                        'tickcolor': "#FFF5E1",
                        'tickfont': {'color': '#FFF5E1'}
                    },
                    'bar': {'color': "#1e3c72"},
                    'bgcolor': "rgba(0,0,0,0)",
                    'borderwidth': 2,
                    'bordercolor': "gray",
                    'steps': [
                        {'range': [0, 5], 'color': 'rgba(76, 175, 80, 0.3)'},
                        {'range': [5, 15], 'color': 'rgba(255, 193, 7, 0.3)'},
                        {'range': [15, 100], 'color': 'rgba(255, 82, 82, 0.3)'}
                    ]
                }
            ),
            row=1, col=3
        )
    
    # Update layout
    fig.update_layout(
        height=400,
        margin=dict(t=100, r=25, l=25, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        font={'color': "#FFF5E1", 'family': "Arial"},
        showlegend=False,
        grid={'rows': 1, 'columns': 3, 'pattern': "independent"}
    )
    
    return fig

def get_status_and_color(z_score=None, prob_default=None):
    """Get status text and color based on score type and value"""
    if z_score is not None:
        if z_score > 2.99:
            return "Safe Zone", "rgba(76, 175, 80, 0.2)", "Strong financial position with low bankruptcy risk."
        elif z_score > 1.81:
            return "Grey Zone", "rgba(255, 193, 7, 0.2)", "Some financial concerns present. Monitor closely."
        else:
            return "Distress Zone", "rgba(255, 82, 82, 0.2)", "High risk of financial distress. Immediate action recommended."
    
    if prob_default is not None:
        if prob_default < 0.3:
            return "Low Risk", "rgba(76, 175, 80, 0.2)", "Strong financial position with low default probability."
        elif prob_default < 0.7:
            return "Moderate Risk", "rgba(255, 193, 7, 0.2)", "Some default risk present. Careful monitoring advised."
        else:
            return "High Risk", "rgba(255, 82, 82, 0.2)", "Significant default risk. Immediate attention required."

# UI Component Functions

def render_header():
    """Render the application header"""
    st.markdown("""
        <div style='text-align: center'>
            <h1 style='color: #FFF5E1'>Financial Health Analyzer</h1>
            <p style='color: #9ca3af; font-size: 1.2rem; margin-bottom: 2rem;'>
                Advanced Bankruptcy Risk Assessment
            </p>
        </div>
    """, unsafe_allow_html=True)

def render_sidebar():
    """Render the sidebar content"""
    with st.sidebar:
        st.image("assets/risk-insights-logo.svg", use_column_width=True)
        st.title("Bankruptcy Risk Analysis")
        
        with st.expander("About Altman Z-Score", expanded=True):
            st.markdown("""
            The Altman Z-Score predicts bankruptcy risk:
            
            🟢 **> 2.99:** Safe Zone
            - Strong financial health
            - Low bankruptcy risk
            
            🟡 **1.81 - 2.99:** Grey Zone
            - Moderate risk
            - Requires attention
            
            🔴 **< 1.81:** Distress Zone
            - High bankruptcy risk
            - Immediate action needed
            """)
        
        with st.expander("About Ohlson O-Score", expanded=True):
            st.markdown("""
            The O-Score calculates probability of default:
            
            🟢 **< 30%:** Low Risk
            - Strong financial position
            - Low default probability
            
            🟡 **30-70%:** Moderate Risk
            - Caution needed
            - Monitor closely
            
            🔴 **> 70%:** High Risk
            - Significant concerns
            - Immediate attention required
            """)

class SearchState:
    """Class to manage search state"""
    def __init__(self):
        if 'selected_company' not in st.session_state:
            st.session_state.selected_company = None
        if 'search_query' not in st.session_state:
            st.session_state.search_query = ""
        if 'selected_index' not in st.session_state:
            st.session_state.selected_index = -1
        if 'should_analyze' not in st.session_state:
            st.session_state.should_analyze = False

def get_company_suggestions(query: str) -> List[Dict[str, str]]:
    """Get company suggestions based on user input"""
    if not query or len(query) < 2:
        return []
        
    try:
        url = "https://query2.finance.yahoo.com/v1/finance/search"
        params = {
            'q': query,
            'quotesCount': 6,
            'newsCount': 0,
            'enableFuzzyQuery': True,
            'quotesQueryId': 'tss_match_phrase_query'
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=5)
        data = response.json()
        
        if 'quotes' not in data:
            return []
            
        return [{
            'symbol': quote['symbol'],
            'name': quote.get('shortname', quote.get('longname', 'Unknown Company')),
            'exchange': quote.get('exchange', 'N/A'),
            'type': quote.get('quoteType', 'N/A')
        } for quote in data['quotes'] if 'symbol' in quote]
        
    except Exception as e:
        print(f"Error fetching suggestions: {str(e)}")
        return []

def handle_suggestion_click(suggestion: Dict[str, str]):
    """Handle when a suggestion is clicked"""
    st.session_state.selected_company = suggestion
    st.session_state.search_query = f"{suggestion['symbol']} - {suggestion['name']}"
    st.session_state.should_analyze = True
    st.experimental_rerun()

def render_search_section() -> Tuple[Optional[str], bool]:
    """Render the enhanced search input section with auto-suggest"""
    # Initialize search state
    search_state = SearchState()
    
    st.markdown("""
        <style>
        /* Search Container */
        .search-container {
            position: relative;
            margin-bottom: 20px;
        }
        
        /* Search Input */
        .stTextInput > div > div {
            background-color: #1f2937 !important;
            border-radius: 8px !important;
            border: 1px solid rgba(255,255,255,0.1) !important;
            transition: all 0.3s ease !important;
        }
        
        .stTextInput > div > div:focus-within {
            border-color: #3b82f6 !important;
            box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2) !important;
        }
        
        /* Suggestions Container */
        .suggestions-container {
            position: absolute;
            width: 100%;
            max-height: 300px;
            overflow-y: auto;
            background: #1f2937;
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 8px;
            margin-top: 4px;
            z-index: 1000;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        }
        
        /* Suggestion Item */
        .suggestion-item {
            display: flex;
            align-items: center;
            padding: 12px 16px;
            cursor: pointer;
            transition: all 0.2s ease;
            border-bottom: 1px solid rgba(255,255,255,0.05);
        }
        
        .suggestion-item:last-child {
            border-bottom: none;
        }
        
        .suggestion-item:hover {
            background-color: rgba(59, 130, 246, 0.1);
        }
        
        .suggestion-item.selected {
            background-color: rgba(59, 130, 246, 0.2);
        }
        
        /* Suggestion Content */
        .suggestion-symbol {
            color: #FFF5E1;
            font-weight: 600;
            margin-right: 12px;
            min-width: 70px;
        }
        
        .suggestion-info {
            flex-grow: 1;
        }
        
        .suggestion-name {
            color: #9ca3af;
            font-size: 0.95em;
            display: block;
            margin-bottom: 2px;
        }
        
        .suggestion-details {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 0.85em;
            color: #6b7280;
        }
        
        .suggestion-exchange {
            padding: 2px 6px;
            background: rgba(255,255,255,0.1);
            border-radius: 4px;
        }
        
        .suggestion-type {
            color: #6b7280;
        }
        
        /* Loading State */
        .search-loading {
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 1rem;
            color: #9ca3af;
        }
        
        /* Scrollbar Styling */
        .suggestions-container::-webkit-scrollbar {
            width: 6px;
        }
        
        .suggestions-container::-webkit-scrollbar-track {
            background: #1f2937;
            border-radius: 3px;
        }
        
        .suggestions-container::-webkit-scrollbar-thumb {
            background: #4b5563;
            border-radius: 3px;
        }
        
        .suggestions-container::-webkit-scrollbar-thumb:hover {
            background: #6b7280;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Search header
    st.markdown("""
        <div class="search-container">
            <h2 style='color: #FFF5E1'>Analyze Company Financial Health</h2>
            <p style="color: #9ca3af; margin-bottom: 1.5rem;">
                Search by company name or ticker symbol for comprehensive analysis
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Layout columns
    col1, col2, col3 = st.columns([1,2,1])
    
    with col2:
        # Search input
        search_placeholder = "Search company or ticker (e.g., AAPL, Apple)"
        current_query = st.text_input(
            "",
            value=st.session_state.search_query,
            placeholder=search_placeholder,
            key="company_search",
            on_change=lambda: setattr(st.session_state, 'selected_company', None)
        )
        
        # Get and display suggestions
        if current_query and current_query != st.session_state.search_query:
            st.session_state.search_query = current_query
            suggestions = get_company_suggestions(current_query)
            
            if suggestions:
                st.markdown("<div class='suggestions-container'>", unsafe_allow_html=True)
                
                for idx, suggestion in enumerate(suggestions):
                    suggestion_class = "suggestion-item selected" if idx == st.session_state.selected_index else "suggestion-item"
                    
                    suggestion_html = f"""
                        <div class='{suggestion_class}' 
                             onclick='
                                document.querySelector("button.analyze-button").click();
                                this.style.backgroundColor = "rgba(59, 130, 246, 0.2)";
                             '>
                            <span class='suggestion-symbol'>{suggestion['symbol']}</span>
                            <div class='suggestion-info'>
                                <span class='suggestion-name'>{suggestion['name']}</span>
                                <div class='suggestion-details'>
                                    <span class='suggestion-exchange'>{suggestion['exchange']}</span>
                                    <span class='suggestion-type'>{suggestion['type']}</span>
                                </div>
                            </div>
                        </div>
                    """
                    
                    if st.markdown(suggestion_html, unsafe_allow_html=True):
                        handle_suggestion_click(suggestion)
                
                st.markdown("</div>", unsafe_allow_html=True)
            elif len(current_query) >= 2:
                st.info("No matching companies found.")
        
        # Hidden button for suggestion clicks
        st.markdown("""
            <button class='analyze-button' style='display: none;'></button>
        """, unsafe_allow_html=True)
        
        # Analysis button
        analyze_button = st.button(
            "Analyze Company",
            use_container_width=True,
            disabled=not (current_query or st.session_state.selected_company)
        )
        
        # Check if we should trigger analysis
        should_analyze = analyze_button or st.session_state.should_analyze
        if should_analyze:
            st.session_state.should_analyze = False
            
            # Get the ticker to analyze
            ticker_to_analyze = None
            if st.session_state.selected_company:
                ticker_to_analyze = st.session_state.selected_company['symbol']
            elif current_query:
                # Try to extract ticker from query
                parts = current_query.split(' - ')
                ticker_to_analyze = parts[0].strip()
            
            return ticker_to_analyze, True
        
        return None, False


def calculate_z_score(ticker):
    """
    Calculate Altman Z-Score with error handling and alternative calculations
    Returns: z_score, problematic_values, substituted_values
    """
    problematic_values = []
    substituted_values = []
    
    try:
        company = yf.Ticker(ticker)
        balance_sheet = company.balance_sheet
        income_stmt = company.income_stmt
        info = company.info

        # Total Assets (A)
        total_assets, _ = safe_get(balance_sheet, ['Total Assets', 'TotalAssets'])
        if is_problematic(total_assets):
            current_assets, _ = safe_get(balance_sheet, ['Current Assets', 'TotalCurrentAssets'])
            non_current_assets, _ = safe_get(balance_sheet, ['Non Current Assets', 'TotalNonCurrentAssets'])
            total_assets = current_assets + non_current_assets
            if not is_problematic(total_assets):
                substituted_values.append("Total Assets (calculated from Current + Non-Current Assets)")
            else:
                problematic_values.append("Total Assets")
                return None, problematic_values, substituted_values

        # Working Capital
        current_assets, _ = safe_get(balance_sheet, ['Current Assets', 'CurrentAssets', 'TotalCurrentAssets'])
        current_liabilities, _ = safe_get(balance_sheet, ['Current Liabilities', 'CurrentLiabilities', 'TotalCurrentLiabilities'])
        working_capital = current_assets - current_liabilities

        # Retained Earnings
        retained_earnings, _ = safe_get(balance_sheet, ['Retained Earnings', 'RetainedEarnings'])
        if is_problematic(retained_earnings):
            total_equity, _ = safe_get(balance_sheet, ['Total Equity', 'TotalEquity'])
            capital_stock, _ = safe_get(balance_sheet, ['Capital Stock', 'CommonStock'])
            retained_earnings = total_equity - capital_stock
            if not is_problematic(retained_earnings):
                substituted_values.append("Retained Earnings (calculated from Total Equity - Capital Stock)")
            else:
                problematic_values.append("Retained Earnings")

        # EBIT
        ebit, _ = safe_get(income_stmt, ['EBIT', 'OperatingIncome'])
        if is_problematic(ebit):
            ebitda, _ = safe_get(income_stmt, ['EBITDA'])
            depreciation, _ = safe_get(income_stmt, ['Depreciation', 'DepreciationAndAmortization'])
            ebit = ebitda - depreciation
            if not is_problematic(ebit):
                substituted_values.append("EBIT (calculated from EBITDA - Depreciation)")
            else:
                problematic_values.append("EBIT")

        # Market Value of Equity
        market_value = info.get('marketCap', 0)
        if is_problematic(market_value):
            shares = info.get('sharesOutstanding', 0)
            price = info.get('currentPrice', 0)
            market_value = shares * price
            if not is_problematic(market_value):
                substituted_values.append("Market Value (calculated from Shares * Price)")
            else:
                problematic_values.append("Market Value")

        # Total Liabilities
        total_liabilities, _ = safe_get(balance_sheet, [
            'Total Liabilities Net Minority Interest',
            'TotalLiabilities',
            'Total Liabilities'
        ])

        # Sales
        sales, _ = safe_get(income_stmt, ['Total Revenue', 'TotalRevenue', 'Revenue'])
        if is_problematic(sales):
            problematic_values.append("Sales/Revenue")

        # Calculate ratios if we have the minimum required data
        if not is_problematic(total_assets):
            A = working_capital / total_assets
            B = retained_earnings / total_assets
            C = ebit / total_assets
            D = market_value / total_liabilities if not is_problematic(total_liabilities) else 0
            E = sales / total_assets

            # Calculate Z-Score
            z_score = 1.2*A + 1.4*B + 3.3*C + 0.6*D + 1.0*E
            return z_score, problematic_values, substituted_values

    except Exception as e:
        problematic_values.append(f"Calculation Error: {str(e)}")
    
    return None, problematic_values, substituted_values

def calculate_ohlson_score(company):
    """
    Calculate Ohlson's O-Score and probability of default
    Returns: o_score, prob_default, problematic_values, substituted_values
    """
    problematic_values = []
    substituted_values = []
    
    try:
        balance_sheet = company.balance_sheet
        income_stmt = company.income_stmt
        info = company.info

        # Get total assets and apply log transform
        total_assets, _ = safe_get(balance_sheet, ['Total Assets', 'TotalAssets'])
        if is_problematic(total_assets):
            total_assets = sum([
                safe_get(balance_sheet, ['Current Assets', 'TotalCurrentAssets'])[0],
                safe_get(balance_sheet, ['Non Current Assets', 'TotalNonCurrentAssets'])[0]
            ])
            if not is_problematic(total_assets):
                substituted_values.append("Total Assets (sum of Current and Non-Current)")
            else:
                problematic_values.append("Total Assets")
                return None, None, problematic_values, substituted_values

        size = math.log(max(total_assets, 10000))

        # Calculate working capital items
        current_assets, _ = safe_get(balance_sheet, ['Current Assets', 'TotalCurrentAssets'])
        current_liabilities, _ = safe_get(balance_sheet, ['Current Liabilities', 'TotalCurrentLiabilities'])
        working_capital = current_assets - current_liabilities
        
        # Get total liabilities
        total_liabilities, _ = safe_get(balance_sheet, [
            'Total Liabilities Net Minority Interest',
            'TotalLiabilities'
        ])

        # Calculate key ratios
        tlta = total_liabilities / total_assets if not is_problematic(total_liabilities) else 0
        wcta = working_capital / total_assets
        clca = current_liabilities / current_assets if not is_problematic(current_assets) else 0
        oeneg = 1 if total_liabilities > total_assets else 0

        # Get net income
        net_income, _ = safe_get(income_stmt, ['Net Income', 'NetIncome'])
        if is_problematic(net_income):
            operating_income, _ = safe_get(income_stmt, ['Operating Income', 'OperatingIncome'])
            interest_expense, _ = safe_get(income_stmt, ['Interest Expense', 'InterestExpense'])
            tax_expense, _ = safe_get(income_stmt, ['Tax Provision', 'TaxProvision'])
            net_income = operating_income - interest_expense - tax_expense
            if not is_problematic(net_income):
                substituted_values.append("Net Income (Operating Income - Interest - Tax)")
            else:
                problematic_values.append("Net Income")

        nita = net_income / total_assets if not is_problematic(net_income) else 0

        # Get previous year's net income for change calculation
        try:
            prev_net_income, _ = safe_get(income_stmt, ['Net Income', 'NetIncome'], index=1)
            intwo = 1 if net_income < 0 and prev_net_income < 0 else 0
            chin = (net_income - prev_net_income) / (abs(net_income) + abs(prev_net_income))
        except:
            intwo = 0
            chin = 0
            substituted_values.append("Previous year's data not available")

        # Calculate O-Score
        o_score = (-1.32 - 0.407*size + 6.03*tlta - 1.43*wcta + 0.0757*clca 
                  + 2.37*oeneg - 1.83*nita + 0.285*intwo - 1.72*oeneg - 0.521*chin)

        # Calculate probability of default
        prob_default = 1 / (1 + math.exp(-o_score))

        return o_score, prob_default, problematic_values, substituted_values

    except Exception as e:
        problematic_values.append(f"Calculation Error: {str(e)}")
        return None, None, problematic_values, substituted_values

def calculate_merton_default(company):
    """
    Calculate probability of default using Merton's model with comprehensive error handling
    Returns: prob_default, distance_to_default, problematic_values, substituted_values
    """
    problematic_values = []
    substituted_values = []
    
    try:
        # Get stock data for volatility calculation
        try:
            stock_data = company.history(period="1y")
            if len(stock_data) < 30:  # Try shorter period if 1y not available
                stock_data = company.history(period="6mo")
                if len(stock_data) < 30:
                    stock_data = company.history(period="3mo")
                    if len(stock_data) < 30:
                        problematic_values.append("Insufficient stock price history")
                        return None, None, problematic_values, substituted_values
                    else:
                        substituted_values.append("Using 3-month price history for volatility")
                else:
                    substituted_values.append("Using 6-month price history for volatility")
        except Exception as e:
            problematic_values.append(f"Error fetching stock data: {str(e)}")
            return None, None, problematic_values, substituted_values

        # Calculate equity volatility (annualized)
        try:
            # Try different methods for volatility calculation
            returns = np.log(stock_data['Close'] / stock_data['Close'].shift(1))
            if returns.std() == 0 or np.isnan(returns.std()):
                # Try alternative price points
                returns = np.log(stock_data['Adj Close'] / stock_data['Adj Close'].shift(1))
                if returns.std() == 0 or np.isnan(returns.std()):
                    # Try using high-low range as volatility proxy
                    returns = np.log(stock_data['High'] / stock_data['Low'])
                    substituted_values.append("Using high-low range for volatility calculation")
                else:
                    substituted_values.append("Using adjusted close prices for volatility")
            
            equity_vol = returns.std() * np.sqrt(252)  # Annualize daily volatility
            
            if np.isnan(equity_vol) or equity_vol == 0:
                # Use industry average or historical average as fallback
                equity_vol = 0.3  # Typical market volatility
                substituted_values.append("Using market average volatility (0.3)")
        except Exception as e:
            problematic_values.append(f"Error calculating volatility: {str(e)}")
            return None, None, problematic_values, substituted_values

        # Get balance sheet and income statement data
        balance_sheet = company.balance_sheet
        income_stmt = company.income_stmt
        info = company.info

        # Market value of equity (E)
        market_cap = info.get('marketCap', 0)
        if is_problematic(market_cap):
            # Try alternative calculations
            shares = info.get('sharesOutstanding', 0)
            if is_problematic(shares):
                shares = info.get('floatShares', 0)
                if not is_problematic(shares):
                    substituted_values.append("Using float shares instead of shares outstanding")
            
            price = info.get('currentPrice', 0)
            if is_problematic(price):
                price = stock_data['Close'].iloc[-1]
                substituted_values.append("Using latest closing price")
            
            market_cap = shares * price
            if not is_problematic(market_cap):
                substituted_values.append("Market Cap (calculated from Shares * Price)")
            else:
                # Try book value as last resort
                total_equity, _ = safe_get(balance_sheet, ['Total Equity', 'TotalEquity'])
                if not is_problematic(total_equity):
                    market_cap = total_equity * 1.1  # Assuming small premium to book
                    substituted_values.append("Using book value of equity with premium")
                else:
                    problematic_values.append("Market Value of Equity")
                    return None, None, problematic_values, substituted_values

        # Face value of debt (F)
        total_liabilities, _ = safe_get(balance_sheet, [
            'Total Liabilities Net Minority Interest',
            'TotalLiabilities',
            'Total Liabilities'
        ])
        if is_problematic(total_liabilities):
            # Try summing components
            current_liabilities, _ = safe_get(balance_sheet, ['Current Liabilities', 'TotalCurrentLiabilities'])
            long_term_debt, _ = safe_get(balance_sheet, ['Long Term Debt', 'LongTermDebt'])
            total_liabilities = current_liabilities + long_term_debt
            
            if not is_problematic(total_liabilities):
                substituted_values.append("Total Liabilities (sum of current liabilities and long-term debt)")
            else:
                # Try other debt measures
                total_debt, _ = safe_get(balance_sheet, ['Total Debt', 'TotalDebt'])
                if not is_problematic(total_debt):
                    total_liabilities = total_debt * 1.2  # Assuming some non-debt liabilities
                    substituted_values.append("Using total debt with adjustment for non-debt liabilities")
                else:
                    problematic_values.append("Total Liabilities")
                    return None, None, problematic_values, substituted_values

        # Risk-free rate (use 1-year Treasury rate or alternatives)
        try:
            rf_rate = 0.05  # Can be updated with actual Treasury rate API
        except:
            rf_rate = 0.05  # Default to 5% if unable to fetch
            substituted_values.append("Using default 5% risk-free rate")

        # Time horizon
        T = 1.0  # 1 year

        # Calculate implied asset value and volatility using iterative process
        V_A = market_cap + total_liabilities  # Initial guess
        sigma_A = equity_vol * market_cap / V_A  # Initial guess
        
        # Iteration control parameters
        max_iterations = 100
        convergence_threshold = 0.0001
        converged = False

        # Iterate to find asset value and volatility
        for i in range(max_iterations):
            try:
                d1 = (np.log(V_A/total_liabilities) + (rf_rate + 0.5*sigma_A**2)*T) / (sigma_A*np.sqrt(T))
                d2 = d1 - sigma_A*np.sqrt(T)
                
                V_A_new = market_cap / norm.cdf(d1)
                sigma_A_new = equity_vol * market_cap / (V_A * norm.cdf(d1))
                
                if abs(V_A_new - V_A) < convergence_threshold and abs(sigma_A_new - sigma_A) < convergence_threshold:
                    converged = True
                    break
                    
                V_A = 0.5 * (V_A + V_A_new)
                sigma_A = 0.5 * (sigma_A + sigma_A_new)

            except Exception as e:
                problematic_values.append(f"Convergence error in iteration {i}: {str(e)}")
                # Use last valid values
                break

        if not converged:
            substituted_values.append("Using last iteration values (no convergence)")

        try:
            # Calculate distance to default
            distance_to_default = (np.log(V_A/total_liabilities) + (rf_rate - 0.5*sigma_A**2)*T) / (sigma_A*np.sqrt(T))
            
            # Calculate probability of default
            prob_default = norm.cdf(-distance_to_default)
            
            # Sanity checks
            if prob_default > 0.99:
                prob_default = 0.99
                substituted_values.append("Capped probability at 99%")
            elif prob_default < 0.01:
                prob_default = 0.01
                substituted_values.append("Floored probability at 1%")
                
            return prob_default, distance_to_default, problematic_values, substituted_values

        except Exception as e:
            problematic_values.append(f"Error in final probability calculation: {str(e)}")
            return None, None, problematic_values, substituted_values

    except Exception as e:
        problematic_values.append(f"Merton Model Calculation Error: {str(e)}")
        return None, None, problematic_values, substituted_values

def main():
    """Main application function"""
    try:
        # Initialize login system
        initialize_login_system()
        
        # Setup UI components
        render_header()
        render_sidebar()
        
        # Get search results
        ticker, should_analyze = render_search_section()
        
        # Process analysis if triggered
        if should_analyze:
            if not ticker:
                st.warning("Please select a company to analyze.")
                return
                
            with st.spinner(f"Analyzing {ticker.upper()}..."):
                try:
                    # Your existing analysis code...
                    company = yf.Ticker(ticker)
                    info = company.info
                    
                    # Display company header immediately after fetch
                    st.markdown(f"""
                    <div class='company-header'>
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <h2 style="margin: 0;">{info.get('longName', ticker.upper())}</h2>
                                <p style="color: #94a3b8; margin-top: 0.5rem;">
                                    {info.get('sector', 'N/A')} | {info.get('industry', 'N/A')}
                                </p>
                            </div>
                            <div style="text-align: right;">
                                <p style="color: #94a3b8; margin: 0;">Market Cap</p>
                                <h3 style="margin: 0;">${info.get('marketCap', 0):,.0f}</h3>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # Calculate scores
                    z_score, z_problematic, z_substituted = calculate_z_score(ticker)
                    o_score, prob_default, o_problematic, o_substituted = calculate_ohlson_score(company)
                    merton_prob, distance_to_default, merton_problematic, merton_substituted = calculate_merton_default(company)

                    # Display scores and analysis if calculations were successful
                    # To this more flexible condition:
                    if any([z_score is not None, prob_default is not None, merton_prob is not None]):
                        st.plotly_chart(create_gauge_charts(z_score, prob_default, merton_prob), 
                                       use_container_width=True)

                        # Risk Assessment
                        risk_col1, risk_col2, risk_col3 = st.columns(3)
                        
                        with risk_col1:
                            if z_score is not None:
                                status, color, desc = get_status_and_color(z_score=z_score)
                                st.markdown(f"""
                                <div style="background: {color}; padding: 15px; border-radius: 10px;">
                                    <h3 style="color: #FFF5E1; margin: 0;">Z-Score Analysis</h3>
                                    <p style="color: #FFF5E1; margin: 10px 0;">Score: {z_score:.2f} - {status}</p>
                                    <p style="color: #9ca3af; margin: 0;">{desc}</p>
                                </div>
                                """, unsafe_allow_html=True)
                        
                        with risk_col2:
                            if prob_default is not None:
                                status, color, desc = get_status_and_color(prob_default=prob_default)
                                st.markdown(f"""
                                <div style="background: {color}; padding: 15px; border-radius: 10px;">
                                    <h3 style="color: #FFF5E1; margin: 0;">Default Risk Analysis</h3>
                                    <p style="color: #FFF5E1; margin: 10px 0;">
                                        Probability: {prob_default*100:.1f}% - {status}
                                    </p>
                                    <p style="color: #9ca3af; margin: 0;">{desc}</p>
                                </div>
                                """, unsafe_allow_html=True)
                        
                        with risk_col3:
                            if merton_prob is not None:
                                st.markdown(f"""
                                <div style="background: {get_merton_color(merton_prob)}; padding: 15px; border-radius: 10px;">
                                    <h3 style="color: #FFF5E1; margin: 0;">Merton Model Analysis</h3>
                                    <p style="color: #FFF5E1; margin: 10px 0;">
                                        Default Probability: {merton_prob*100:.1f}%
                                    </p>
                                    <p style="color: #FFF5E1; margin: 10px 0;">
                                        Distance to Default: {distance_to_default:.2f}
                                    </p>
                                    <p style="color: #9ca3af; margin: 0;">
                                        Based on market-based structural model of credit risk.
                                    </p>
                                </div>
                                """, unsafe_allow_html=True)

                        # Financial Metrics
                        st.markdown("""<h2 style='color: #FFF5E1; margin-top: 30px;'>Key Financial Metrics</h2>""", 
                                  unsafe_allow_html=True)
                        
                        metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
                        metrics = [
                            ("Revenue Growth", f"{info.get('revenueGrowth', 0)*100:.1f}%"),
                            ("Profit Margin", f"{info.get('profitMargins', 0)*100:.1f}%"),
                            ("Debt to Equity", f"{info.get('debtToEquity', 0):.2f}")
                        ]

                        for col, (label, value) in zip([metrics_col1, metrics_col2, metrics_col3], metrics):
                            with col:
                                st.markdown(f"""
                                <div class="metric-card">
                                    <div class="metric-label">{label}</div>
                                    <div class="metric-value">{value}</div>
                                </div>
                                """, unsafe_allow_html=True)

                        # Company Details Expander
                        with st.expander("View Detailed Company Information"):
                            st.markdown(f"""
                            <div class="metric-card">
                                <h3>Company Overview</h3>
                                <p style="color: #9ca3af;">{info.get('longBusinessSummary', 'No description available.')}</p>
                                <div style="margin-top: 20px;">
                                    <h4>Additional Details</h4>
                                    <ul style="color: #9ca3af;">
                                        <li>Exchange: {info.get('exchange', 'N/A')}</li>
                                        <li>Industry: {info.get('industry', 'N/A')}</li>
                                        <li>Sector: {info.get('sector', 'N/A')}</li>
                                        <li>Website: <a href="{info.get('website', '#')}" target="_blank">{info.get('website', 'N/A')}</a></li>
                                    </ul>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

                        # Data Quality Notes (if any issues found)
                        
                        # Find this section in the main function where data quality notes are displayed:

                        # Data Quality Notes (if any issues found)
                        if any([z_problematic, z_substituted, o_problematic, o_substituted, merton_problematic, merton_substituted]):  # Updated condition
                            with st.expander("View Data Quality Notes"):
                                # Change from 2 columns to 3
                                qual_col1, qual_col2, qual_col3 = st.columns(3)
                                
                                with qual_col1:
                                    if z_problematic or z_substituted:
                                        st.markdown("""
                                        <div style='background: rgba(0,0,0,0.2); padding: 15px; border-radius: 10px;'>
                                            <h4 style='color: #FFF5E1; margin: 0;'>Z-Score Data Notes</h4>
                                        """, unsafe_allow_html=True)
                                        
                                        for issue in z_problematic:
                                            st.warning(f"⚠️ {issue}")
                                        for sub in z_substituted:
                                            st.info(f"ℹ️ {sub}")
                                        
                                        st.markdown("</div>", unsafe_allow_html=True)
                                
                                with qual_col2:
                                    if o_problematic or o_substituted:
                                        st.markdown("""
                                        <div style='background: rgba(0,0,0,0.2); padding: 15px; border-radius: 10px;'>
                                            <h4 style='color: #FFF5E1; margin: 0;'>O-Score Data Notes</h4>
                                        """, unsafe_allow_html=True)
                                        
                                        for issue in o_problematic:
                                            st.warning(f"⚠️ {issue}")
                                        for sub in o_substituted:
                                            st.info(f"ℹ️ {sub}")
                                        
                                        st.markdown("</div>", unsafe_allow_html=True)
                                
                                with qual_col3:  # New column for Merton model notes
                                    if merton_problematic or merton_substituted:
                                        st.markdown("""
                                        <div style='background: rgba(0,0,0,0.2); padding: 15px; border-radius: 10px;'>
                                            <h4 style='color: #FFF5E1; margin: 0;'>Merton Model Data Notes</h4>
                                        """, unsafe_allow_html=True)
                                        
                                        for issue in merton_problematic:
                                            st.warning(f"⚠️ {issue}")
                                        for sub in merton_substituted:
                                            st.info(f"ℹ️ {sub}")
                                        
                                        st.markdown("</div>", unsafe_allow_html=True)

                except Exception as e:
                    st.error(f"Error analyzing company: {str(e)}")
                    st.markdown("""
                    <div style="background: rgba(255,0,0,0.1); padding: 15px; border-radius: 10px;">
                        <h4 style="color: #ff6b6b; margin: 0;">Troubleshooting Tips:</h4>
                        <ul style="color: #9ca3af;">
                            <li>Verify the ticker symbol is correct</li>
                            <li>Ensure the company is publicly traded</li>
                            <li>Check if financial data is available for this company</li>
                        </ul>
                    </div>
                    """, unsafe_allow_html=True)

        # Footer (always shown)
        st.markdown("""
        <div style='text-align: center; color: #9ca3af; padding: 2rem 0;'>
            <p>Data sourced from Yahoo Finance • Last updated: {}</p>
        </div>
        """.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")), unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Application Error: {str(e)}")
        st.write("Please refresh the page and try again.")

if __name__ == "__main__":
    main()
