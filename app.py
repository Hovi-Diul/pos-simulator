import streamlit as st
import pandas as pd

st.set_page_config(page_title="ICARD POS Commission Simulator", layout="wide")

st.title("💳 POS Commission & Profit Simulator")
st.markdown("Interactive calculator for simulating revenues, costs, and commissions before signing a contract.")

# ==========================================
# HIDDEN INTERNAL ICARD COSTS (BACKEND)
# Distributors cannot see or modify these!
# ==========================================
HIDDEN_COSTS = {
    "VS/MC/Maestro consumer debit": {
        "variable": 0.1010,   # %
        "fixed": 0.0116,      # € per transaction
        "interchange": 0.20 # %
    },
    "VS/MC/Maestro consumer credit": {
        "variable": 0.1060,
        "fixed": 0.0116,
        "interchange": 0.30
    },
    "VS/MC/Maestro commercial": {
        "variable": 0.2422,
        "fixed": 0.0202,
        "interchange": 1.50
    }
}

st.markdown("---")
st.subheader("📊 Distributor Scenario Input")
st.markdown("Select a card type, enter the average transaction amount, number of transactions, and proposed Merchant Fee (%).")

# Initial table data visible and editable by the distributor
default_user_data = pd.DataFrame([
    {
        "Card Type": "VS/MC/Maestro consumer debit",
        "Transaction Amount (€)": 50.0,  # Average amount per transaction
        "Number of Transactions": 1000,   # Number of transactions
        "Merchant Fee (%)": 1.10
    },
    {
        "Card Type": "VS/MC/Maestro consumer credit",
        "Transaction Amount (€)": 100.0,
        "Number of Transactions": 300,
        "Merchant Fee (%)": 1.50
    },
    {
        "Card Type": "VS/MC/Maestro commercial",
        "Transaction Amount (€)": 200.0,
        "Number of Transactions": 100,
        "Merchant Fee (%)": 2.00
    }
])

# Editable table for the distributor
edited_df = st.data_editor(default_user_data, num_rows="dynamic", use_container_width=True)

# Calculations with automatic lookup of hidden backend costs
if not edited_df.empty:
    df = edited_df.copy()
    
    # Map hidden costs based on selected Card Type
    df["Variable Component (%)"] = df["Card Type"].map(lambda x: HIDDEN_COSTS.get(x, {"variable": 0})["variable"])
    df["Fixed Component (€/tx)"] = df["Card Type"].map(lambda x: HIDDEN_COSTS.get(x, {"fixed": 0})["fixed"])
    df["Interchange Fee (%)"] = df["Card Type"].map(lambda x: HIDDEN_COSTS.get(x, {"interchange": 0})["interchange"])
    
    # Total volume per card = Transaction Amount × Number of Transactions
    df["Total Volume (€)"] = df["Transaction Amount (€)"] * df["Number of Transactions"]
    
    # Formulas
    df["Collected Merchant Fee (€)"] = df["Total Volume (€)"] * (df["Merchant Fee (%)"] / 100)
    
    df["Total Cost (€)"] = (
        (df["Total Volume (€)"] * (df["Variable Component (%)"] / 100)) +
        (df["Number of Transactions"] * df["Fixed Component (€/tx)"]) +
        (df["Total Volume (€)"] * (df["Interchange Fee (%)"] / 100))
    )
    
    df["Profit ICARD (€)"] = df["Collected Merchant Fee (€)"] - df["Total Cost (€)"]
    df["Agent Commission (30%) (€)"] = df["Profit ICARD (€)"] * 0.30

    st.markdown("---")
    st.subheader("📈 Financial Results")

    result_df = pd.DataFrame({
        "Card Type": df["Card Type"],
        "Total Volume (€)": df["Total Volume (€)"],
        "Number of Transactions": df["Number of Transactions"],
        "Merchant Fee (%)": df["Merchant Fee (%)"],
        "Collected Merchant Fee (€)": df["Collected Merchant Fee (€)"],
        "Agent Commission (€)": df["Agent Commission (30%) (€)"]
    })

    numeric_cols = [
        "Total Volume (€)", 
        "Number of Transactions",
        "Merchant Fee (%)",
        "Collected Merchant Fee (€)", 
        "Agent Commission (€)"
    ]
    
    st.dataframe(result_df.style.format("{:.2f}", subset=numeric_cols), use_container_width=True)

    # Summary KPIs across all rows/card types
    total_turnover = df["Total Volume (€)"].sum()
    total_collected = df["Collected Merchant Fee (€)"].sum()
    total_agent_comm = df["Agent Commission (30%) (€)"].sum()

    st.markdown("---")
    st.subheader("📌 Simulation Summary")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Volume", f"€{total_turnover:,.2f}")
    col2.metric("Collected Merchant Fee", f"€{total_collected:,.2f}")
    col3.metric("Agent Commission", f"€{total_agent_comm:,.2f}")
