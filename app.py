import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

# -----------------------------------------------------------------------------
# DYNAMIC DATA PARSING
# -----------------------------------------------------------------------------
def parse_scenarios_from_csv(filepath):
    """
    Parses the irregular CSV structure to extract all scenarios.
    Locates blocks by finding 'Cumulative Total Cash Flow' and scanning upwards
    for the Scenario Name and Timeline.
    """
    try:
        # Read without header as the structure is irregular
        df = pd.read_csv(filepath, header=None)
    except FileNotFoundError:
        return None

    scenarios = {}
    
    # 1. Identify all rows containing the target data label
    # This finds every block's cumulative data row
    target_label = "Cumulative Total Cash Flow"
    cumulative_rows = df.index[df[0].astype(str).str.contains(target_label, na=False)].tolist()
    
    for row_idx in cumulative_rows:
        # --- A. Find Scenario Name ---
        # Look upwards for the "Variables" row. The Scenario Name is usually 
        # the row immediately preceding "Variables".
        scenario_name = f"Scenario {row_idx}" # Fallback name
        
        # Search up to 50 rows upwards
        for r in range(row_idx, max(0, row_idx - 50), -1):
            val = str(df.iloc[r, 1]).strip()
            if val == 'Variables':
                # Name is in the row above, column 0
                potential_name = str(df.iloc[r-1, 0]).strip()
                if potential_name and potential_name.lower() != 'nan':
                    scenario_name = potential_name
                break
        
        # --- B. Find Timeline (Years & Quarters) ---
        # Look upwards for the row containing "Q1", "Q2", etc.
        q_row_idx = -1
        for r in range(row_idx, max(0, row_idx - 20), -1):
            row_vals = [str(x) for x in df.iloc[r].values]
            # Check for presence of at least Q1 and Q2 to confirm it's a header
            if 'Q1' in row_vals and 'Q2' in row_vals:
                q_row_idx = r
                break
        
        if q_row_idx != -1:
            quarters_row = df.iloc[q_row_idx]
            years_row = df.iloc[q_row_idx - 1] # Years are row above Quarters
            data_row = df.iloc[row_idx]        # The Cumulative Cash Flow row
            
            timeline = []
            values = []
            current_year = ""
            
            # Iterate columns (skip col 0 which is labels)
            for c in range(1, len(quarters_row)):
                y_val = str(years_row[c]).strip()
                q_val = str(quarters_row[c]).strip()
                
                # Update current year if a new one is found (e.g. "CY2024 (2300 units)")
                if "CY20" in y_val:
                    current_year = y_val.split(' ')[0] # Extract just "CY2024"
                
                # Valid Quarter Column?
                if q_val in ['Q1', 'Q2', 'Q3', 'Q4']:
                    # Build Timeline Label
                    timeline.append(f"{current_year} {q_val}")
                    
                    # Extract & Clean Data Value
                    raw_val = str(data_row[c])
                    # Remove currency symbols, 'k' for thousands, commas, and '-'
                    clean_val = raw_val.replace('$', '').replace(',', '').replace('-', '0')
                    
                    # Handle 'k' (e.g., $100k -> 100000)
                    if 'k' in clean_val.lower():
                        clean_val = clean_val.lower().replace('k', '')
                        multiplier = 1000
                    else:
                        multiplier = 1
                        
                    try:
                        final_val = float(clean_val) * multiplier
                        values.append(final_val)
                    except ValueError:
                        values.append(0.0)
            
            # Store extracted data
            scenarios[scenario_name] = {
                "timeline": timeline,
                "values": values
            }
            
    return scenarios

# -----------------------------------------------------------------------------
# STREAMLIT APP
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Purchase Plan Cash Flow", layout="wide")

st.title("FY27 Purchase Plan: Cumulative Cash Flow")
st.markdown("### Scenario Comparison")

# --- FILE LOADING ---
# Try to load the specific file automatically
default_file = 'FY27 Purchase Plan (Brandon).csv'
data = parse_scenarios_from_csv(default_file)

if not data:
    st.error(f"Could not find '{default_file}'. Please ensure the file is in the same directory.")
    uploaded_file = st.file_uploader("Or upload the file manually:", type=['csv'])
    if uploaded_file:
        # Save temp to parse
        with open("temp_upload.csv", "wb") as f:
            f.write(uploaded_file.getbuffer())
        data = parse_scenarios_from_csv("temp_upload.csv")

# --- VISUALIZATION ---
if data:
    # --- CONTROLS ---
    col1, col2 = st.columns([1, 4])
    
    with col1:
        st.subheader("Configuration")
        
        st.write(f"**Found {len(data)} Scenarios**")
        
        all_scenarios = list(data.keys())
        selected_scenarios = []
        
        st.write("Select Scenarios:")
        for sc in all_scenarios:
            if st.checkbox(sc, value=True):
                selected_scenarios.append(sc)

    # --- PROCESS DATA FOR PLOTTING ---
    plot_data = []
    final_totals = {}
    
    for sc_name in selected_scenarios:
        sc_data = data[sc_name]
        df = pd.DataFrame({
            "Period": sc_data["timeline"],
            "Cumulative Cash Flow": sc_data["values"]
        })
        
        # Store final total for metrics (last value)
        if not df.empty:
            final_totals[sc_name] = df["Cumulative Cash Flow"].iloc[-1]
            
        plot_data.append({
            "name": sc_name,
            "df": df
        })

    with col2:
        if not plot_data:
            st.warning("Please select at least one scenario.")
        else:
            # 1. Metrics Row
            # Display metrics in a grid
            st.markdown("#### Final Cumulative Totals")
            metric_cols = st.columns(min(len(plot_data), 4)) # Max 4 cols per row
            
            for i, item in enumerate(plot_data):
                col_idx = i % 4
                with metric_cols[col_idx]:
                    total = final_totals.get(item["name"], 0)
                    # Shorten name for display if really long
                    display_name = item["name"].split(',')[0] 
                    st.metric(label=display_name, value=f"${total:,.0f}")
            
            # 2. Main Chart
            fig = go.Figure()
            
            for item in plot_data:
                df = item["df"]
                fig.add_trace(go.Scatter(
                    x=df["Period"],
                    y=df["Cumulative Cash Flow"],
                    mode='lines+markers',
                    name=item["name"],
                    line=dict(width=3),
                    hovertemplate=f"<b>{item['name']}</b><br>%{{x}}<br>Total: $%{{y:,.0f}}<extra></extra>"
                ))

            fig.update_layout(
                title="Cumulative Cash Flow Projection",
                xaxis_title="Timeline",
                yaxis_title="Cumulative Cost (USD)",
                yaxis=dict(tickformat="$,.0f"),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.5,
                    xanchor="center",
                    x=0.5
                ),
                hovermode="x unified",
                height=600,
                margin=dict(l=40, r=40, t=80, b=80)
            )
            
            st.plotly_chart(fig, use_container_width=True)

    # --- RAW DATA TABLE ---
    with st.expander("View Consolidated Data Table"):
        if plot_data:
            # Create a merged dataframe for easy viewing
            base_df = plot_data[0]["df"][["Period"]].copy()
            for item in plot_data:
                temp = item["df"].rename(columns={"Cumulative Cash Flow": item["name"]})
                base_df = pd.merge(base_df, temp, on="Period", how="left")
            
            st.dataframe(base_df.set_index("Period").style.format("${:,.0f}"), use_container_width=True)
else:
    st.info("Waiting for data...")
