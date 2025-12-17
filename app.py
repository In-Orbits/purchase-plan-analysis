import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# -----------------------------------------------------------------------------
# EMBEDDED DATA (Extracted from FY27 Purchase Plan)
# -----------------------------------------------------------------------------
DATA_EXPORT = {
    "35% Rigado Replacement, 1500 Annual Demand": {
        "timeline": [
            "CY2024 Q1", "CY2024 Q2", "CY2024 Q3", "CY2024 Q4",
            "CY2025 Q1", "CY2025 Q2", "CY2025 Q3", "CY2025 Q4",
            "CY2026 Q1", "CY2026 Q2", "CY2026 Q3", "CY2026 Q4",
            "CY2027 Q1", "CY2027 Q2", "CY2027 Q3", "CY2027 Q4",
            "CY2028 Q1", "CY2028 Q2", "CY2028 Q3", "CY2028 Q4"
        ],
        "quarterly_values": [
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
        "quarterly_values": [
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
        "quarterly_values": [
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
st.markdown("### Cumulative Cash Flow Scenarios")

# --- CONTROLS ---
col1, col2 = st.columns([1, 4])

with col1:
    st.subheader("Settings")
    
    # Defaulting to Cumulative as requested
    view_mode = st.radio(
        "Metric:", 
        ["Cumulative Cash Flow", "Quarterly Cash Flow"],
        index=0
    )
    
    st.markdown("---")
    st.write("**Scenarios:**")
    
    all_scenarios = list(DATA_EXPORT.keys())
    selected_scenarios = []
    
    # Create a checkbox for each scenario to allow easy toggling
    for sc in all_scenarios:
        if st.checkbox(sc, value=True):
            selected_scenarios.append(sc)

# --- DATA PROCESSING ---
plot_data = []
final_totals = {}

for scenario_name in selected_scenarios:
    data = DATA_EXPORT[scenario_name]
    df = pd.DataFrame({
        "Period": data["timeline"],
        "Quarterly Cash Flow": data["quarterly_values"]
    })
    
    # Calculate Cumulative
    df["Cumulative Cash Flow"] = df["Quarterly Cash Flow"].cumsum()
    
    # Store final total for metrics
    final_totals[scenario_name] = df["Cumulative Cash Flow"].iloc[-1]
    
    plot_data.append({
        "name": scenario_name,
        "df": df
    })

# --- VISUALIZATION ---
with col2:
    if not plot_data:
        st.warning("Select at least one scenario to view the chart.")
    else:
        # 1. Summary Metrics (Top of chart)
        if view_mode == "Cumulative Cash Flow":
            cols = st.columns(len(plot_data))
            for idx, item in enumerate(plot_data):
                with cols[idx]:
                    total = final_totals[item["name"]]
                    # Shorten name for metric label if needed
                    short_name = item["name"].split(",")[0] 
                    st.metric(label=short_name, value=f"${total:,.0f}")

        # 2. Main Chart
        fig = go.Figure()
        
        for item in plot_data:
            df = item["df"]
            y_col = view_mode
            
            # Add trace
            fig.add_trace(go.Scatter(
                x=df["Period"],
                y=df[y_col],
                mode='lines+markers',
                name=item["name"],
                line=dict(width=3),
                hovertemplate=f"<b>{item['name']}</b><br>Period: %{{x}}<br>{view_mode}: $%{{y:,.0f}}<extra></extra>"
            ))

        fig.update_layout(
            title=f"{view_mode} Over Time",
            xaxis_title="Timeline",
            yaxis_title="Amount (USD)",
            yaxis=dict(tickformat="$,.0f"),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.3, # Move legend below chart
                xanchor="center",
                x=0.5
            ),
            hovermode="x unified",
            height=600,
            margin=dict(l=40, r=40, t=80, b=80)
        )
        
        st.plotly_chart(fig, use_container_width=True)

# --- RAW DATA TABLE ---
with st.expander("View Raw Data Table"):
    if plot_data:
        # Pivot for cleaner table: Period as index, Scenario columns
        base_df = plot_data[0]["df"][["Period"]].copy()
        
        for item in plot_data:
            y_col = view_mode
            temp_df = item["df"][["Period", y_col]].rename(columns={y_col: item["name"]})
            base_df = pd.merge(base_df, temp_df, on="Period", how="left")
            
        st.dataframe(
            base_df.set_index("Period").style.format("${:,.0f}"),
            use_container_width=True
        )
