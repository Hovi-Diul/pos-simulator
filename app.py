import streamlit as st
import pandas as pd

st.set_page_config(page_title="ICARD POS Commission Simulator", layout="wide")

st.title("POS Commission & Profit Simulator")
st.markdown("Interactive calculator for simulating revenues, costs, and commissions before signing a contract.")

# ==========================================
# HIDDEN INTERNAL ICARD COSTS (BACKEND)
# Distributors cannot see or modify these!
# ==========================================
HIDDEN_COSTS = {
    "Visa/Mastercard/Maestro": {
        "variable": 0.1010,    # %
        "fixed": 0.0116,       # € per transaction
        "interchange": 0.20    # %
    }
}

CARD_OPTIONS = list(HIDDEN_COSTS.keys())

st.markdown("---")
st.subheader("Distributor Scenario Input")
st.markdown("Select a card type, enter the average transaction amount, number of transactions, and proposed Merchant Fee (%).")

# Initial table data visible and editable by the distributor
default_user_data = pd.DataFrame([
    {
        "Card Type": "Visa/Mastercard/Maestro",
        "Transaction Amount (€)": 50.0,      # Average amount per transaction
        "Number of Transactions": 1000,    # Number of transactions
        "Merchant Fee (%)": 1.10
    },
    {
        "Card Type": "Visa/Mastercard/Maestro",
        "Transaction Amount (€)": 100.0,
        "Number of Transactions": 300,
        "Merchant Fee (%)": 1.50
    },
    {
        "Card Type": "Visa/Mastercard/Maestro",
        "Transaction Amount (€)": 200.0,
        "Number of Transactions": 100,
        "Merchant Fee (%)": 2.00
    }
])

# Editable table for the distributor with dropdown for Card Type
edited_df = st.data_editor(
    default_user_data,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "Card Type": st.column_config.SelectboxColumn(
            "Card Type",
            options=CARD_OPTIONS,
            required=True
        )
    }
)

# Calculations with automatic lookup of hidden backend costs
if not edited_df.empty:
    df = edited_df.copy()
    df["Card Type"] = df["Card Type"].fillna(CARD_OPTIONS[0])
    df["Transaction Amount (€)"] = pd.to_numeric(df["Transaction Amount (€)"], errors="coerce").fillna(0.0)
    df["Number of Transactions"] = pd.to_numeric(df["Number of Transactions"], errors="coerce").fillna(0)
    df["Merchant Fee (%)"] = pd.to_numeric(df["Merchant Fee (%)"], errors="coerce").fillna(0.0)

    # Map hidden costs based on selected Card Type
    df["Variable Component (%)"] = df["Card Type"].map(lambda x: HIDDEN_COSTS.get(x, {"variable": 0})["variable"])
    df["Fixed Component (€/tx)"] = df["Card Type"].map(lambda x: HIDDEN_COSTS.get(x, {"fixed": 0})["fixed"])
    df["Interchange Fee (%)"] = df["Card Type"].map(lambda x: HIDDEN_COSTS.get(x, {"interchange": 0})["interchange"])

    # Total turnover per row = Transaction Amount * Number of Transactions
    df["Total Turnover (€)"] = df["Transaction Amount (€)"] * df["Number of Transactions"]

    # Formulas
    df["Collected Fee (€)"] = df["Total Turnover (€)"] * (df["Merchant Fee (%)"] / 100)

    df["Total Cost (€)"] = (
        (df["Total Turnover (€)"] * (df["Variable Component (%)"] / 100)) +
        (df["Number of Transactions"] * df["Fixed Component (€/tx)"]) +
        (df["Total Turnover (€)"] * (df["Interchange Fee (%)"] / 100))
    )

    df["Profit ICARD (€)"] = df["Collected Fee (€)"] - df["Total Cost (€)"]
    df["Agent Commission (€)"] = df["Profit ICARD (€)"] * 0.30

    # Aggregate by Card Type so Total Collected Fee is the sum of all collected fees per card type
    grouped_df = df.groupby("Card Type", as_index=False).agg({
        "Total Turnover (€)": "sum",
        "Collected Fee (€)": "sum",
        "Agent Commission (€)": "sum"
    })

    # Weighted average Merchant Fee (%) per Card Type based on turnover
    grouped_df["Merchant Fee (%)"] = grouped_df.apply(
        lambda row: (row["Collected Fee (€)"] / row["Total Turnover (€)"] * 100) if row["Total Turnover (€)"] > 0 else 0.0,
        axis=1
    )

    result_df = pd.DataFrame({
        "Card Type": grouped_df["Card Type"],
        "Total Turnover (€)": grouped_df["Total Turnover (€)"],
        "Merchant Fee (%)": grouped_df["Merchant Fee (%)"],
        "Total Collected Fee (€)": grouped_df["Collected Fee (€)"],
        "Agent Commission (€)": grouped_df["Agent Commission (€)"]
    })

    st.markdown("---")
    st.subheader("Financial Results")

    numeric_cols = [
        "Total Turnover (€)",
        "Merchant Fee (%)",
        "Total Collected Fee (€)",
        "Agent Commission (€)"
    ]

    st.dataframe(result_df.style.format("{:.2f}", subset=numeric_cols), use_container_width=True)

    # Summary KPIs across all rows/card types
    total_volume = result_df["Total Turnover (€)"].sum()
    total_collected = result_df["Total Collected Fee (€)"].sum()
    total_agent_comm = result_df["Agent Commission (€)"].sum()

    st.markdown("---")
    st.subheader("Simulation Summary")

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Volume", f"€{total_volume:,.2f}")
    col2.metric("Total Collected Fee", f"€{total_collected:,.2f}")
    col3.metric("Agent Commission", f"€{total_agent_comm:,.2f}")
