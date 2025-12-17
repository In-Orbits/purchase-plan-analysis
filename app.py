import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# -----------------------------------------------------------------------------
# EMBEDDED DATA
# -----------------------------------------------------------------------------
# Extracted from "FY27 Purchase Plan (Brandon).csv"
# Scenarios identified:
# 1. 35% Rigado Replacement, 1500 Annual Demand
# 2. 75% Rigado Replacement, 1500 Annual Demand, No Risk buy
# 3. 75% Rigado Replacement, 1750 Annual Demand

DATA_EXPORT = {
    "35% Rigado Replacement, 1500 Annual Demand": {
        "timeline": [
            "CY2024 Q1", "CY2024 Q2", "CY2024 Q3", "CY2024 Q4",
            "CY2025 Q1", "CY2025 Q2", "CY2025 Q3", "CY2025 Q4",
            "CY2026 Q1", "CY2026 Q2", "CY2026 Q3", "CY2026 Q4",
            "CY2027 Q1", "CY2027 Q2", "CY2027 Q3", "CY2027 Q4",
            "CY2028 Q1", "CY2028 Q2", "CY2028 Q3", "CY2028 Q4"
        ],
        # Values in Dollars (extracted from 'Total Cash Flow Out')
        "values": [
            0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0,
            129000.0, 0.0, 129000.0, 0.0,
            129000.0, 0.0, 129000.0, 0.0,
            129000.0, 0.0, 65000.0, 0.0
        ]
    },
    "75% Rigado Replacement, 1500 Annual Demand, No Risk buy": {
        "timeline": [
            "CY2024 Q1", "CY2024 Q2", "CY2024 Q3", "CY2024 Q4",
            "CY2025 Q1", "CY2025 Q2", "CY2025 Q3", "CY2025 Q4",
            "CY2026 Q1", "CY2026 Q2", "CY2026 Q3", "CY2026 Q4",
            "CY2027 Q1", "CY2027 Q2", "CY2027 Q3", "CY2027 Q4",
            "CY2028 Q1", "CY2028 Q2", "CY2028 Q3", "CY2028 Q4"
        ],
        "values": [
            0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0,
            100000.0, 279000.0, 0.0, 129000.0,
            0.0, 129000.0, 0.0, 65000.0,
            0.0, 0.0, 0.0, 0.0
        ]
    },
    "75% Rigado Replacement, 1750 Annual Demand": {
        "timeline": [
            "CY2024 Q1", "CY2024 Q2", "CY2024 Q3", "CY2024 Q4",
            "CY2025 Q1", "CY2025 Q2", "CY2025 Q3", "CY2025 Q4",
            "CY2026 Q1", "CY2026 Q2", "CY2026 Q3", "CY2026 Q4",
            "CY2027 Q1", "CY2027 Q2", "CY2027 Q3", "CY2027 Q4",
            "CY2028 Q1", "CY2028 Q2", "CY2028 Q3", "CY2028 Q4"
        ],
        "values": [
            0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0,
            100000.0, 429000.0, 0.0, 129000.0,
            0.0, 129000.0, 0.0, 258000.0,
            0.0, 129000.0, 0.0, 0.0
        ]
    }
}

# -----------------------------------------------------------------------------
# STREAMLIT APP
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Purchase Plan Cash Flow", layout="wide")

st.title("FY27 Purchase Plan: Cash Flow Analysis")
st.markdown("### Scenario Comparison")

# --- CONTROLS ---
col1, col2 = st.columns([1, 3])

with col1:
    st.subheader("Configuration")
    
    # Checkbox to view Cumulative or Discrete
    view_mode = st.radio("View Mode:", ["Quarterly Cash Flow", "Cumulative Cash Flow"])
    
    # Multi-select for scenarios
    all_scenarios = list(DATA_EXPORT.keys())
    selected_scenarios = st.multiselect(
        "Select Scenarios to Compare:",
        all_scenarios,
        default=all_scenarios  # Default to showing all
    )

# --- DATA PROCESSING ---
plot_data = []

for scenario_name in selected_scenarios:
    data = DATA_EXPORT[scenario_name]
    df = pd.DataFrame({
        "Period": data["timeline"],
        "Cash Flow": data["values"]
    })
    
    # Calculate Cumulative if requested
    df["Cumulative"] = df["Cash Flow"].cumsum()
    
    # Filter out historical zero-data periods if desired (optional cleanup)
    # Keeping full timeline for consistency across scenarios
    
    plot_data.append({
        "name": scenario_name,
        "df": df
    })

# --- VISUALIZATION ---
with col2:
    if not plot_data:
        st.warning("Please select at least one scenario.")
    else:
        fig = go.Figure()
        
        for item in plot_data:
            df = item["df"]
            y_col = "Cumulative" if view_mode == "Cumulative Cash Flow" else "Cash Flow"
            
            fig.add_trace(go.Scatter(
                x=df["Period"],
                y=df[y_col],
                mode='lines+markers',
                name=item["name"],
                hovertemplate=f"<b>{item['name']}</b><br>Period: %{{x}}<br>Amount: $%{{y:,.0f}}<extra></extra>"
            ))

        fig.update_layout(
            title=f"{view_mode} Over Time",
            xaxis_title="Timeline (CY / Quarter)",
            yaxis_title="Amount (USD)",
            yaxis=dict(tickformat="$,.0f"),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            hovermode="x unified",
            height=600
        )
        
        st.plotly_chart(fig, use_container_width=True)

# --- DETAILED DATA TABLE ---
st.divider()
st.subheader("Data Breakdown")

if plot_data:
    # Combine data for table view
    # Pivot logic: Period as index, Scenario Names as columns
    
    # Base timeline from first selected scenario
    base_df = plot_data[0]["df"][["Period"]].copy()
    
    for item in plot_data:
        y_col = "Cumulative" if view_mode == "Cumulative Cash Flow" else "Cash Flow"
        temp_df = item["df"][["Period", y_col]].rename(columns={y_col: item["name"]})
        base_df = pd.merge(base_df, temp_df, on="Period", how="left")
        
    # Formatting for display
    st.dataframe(
        base_df.set_index("Period").style.format("${:,.0f}"),
        use_container_width=True
    )
