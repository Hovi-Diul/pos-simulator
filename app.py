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
    "Visa/Mastercard/Maestro": {
        "variable": 0.1010,   # %
        "fixed": 0.0116,      # € per transaction
        "interchange": 0.20   # %
    }
}

CARD_OPTIONS = list(HIDDEN_COSTS.keys())

st.markdown("---")
st.subheader("📊 Distributor Scenario Input")
st.markdown("Select a card type, enter the average transaction amount, number of transactions, and proposed Merchant Fee (%).")

default_user_data = pd.DataFrame([
    {
        "Card Type": "Visa/Mastercard/Maestro",
        "Transaction Amount (€)": 50.0,
        "Number of Transactions": 1000,
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

edited_df = st.data_editor(
    default_user_data,
    num_rows="dynamic",
    width="stretch",
    column_config={
        "Card Type": st.column_config.SelectboxColumn(
            "Card Type",
            options=CARD_OPTIONS,
            required=True
        ),
        "Transaction Amount (€)": st.column_config.NumberColumn(
            "Transaction Amount (€)",
            min_value=0.0,
            step=1.0,
            format="%.2f"
        ),
        "Number of Transactions": st.column_config.NumberColumn(
            "Number of Transactions",
            min_value=0,
            step=1,
            format="%d"
        ),
        "Merchant Fee (%)": st.column_config.NumberColumn(
            "Merchant Fee (%)",
            min_value=0.0,
            step=0.05,
            format="%.2f"
        )
    }
)

if edited_df is not None and not edited_df.empty:
    df = edited_df.copy()
    df["Card Type"] = df["Card Type"].fillna(CARD_OPTIONS[0]).astype(str)
    df["Transaction Amount (€)"] = pd.to_numeric(df["Transaction Amount (€)"], errors="coerce").fillna(0.0)
    df["Number of Transactions"] = pd.to_numeric(df["Number of Transactions"], errors="coerce").fillna(0.0)
    df["Merchant Fee (%)"] = pd.to_numeric(df["Merchant Fee (%)"], errors="coerce").fillna(0.0)

    # Map hidden costs based on selected Card Type
    df["Variable Component (%)"] = df["Card Type"].map(lambda x: HIDDEN_COSTS.get(x, {"variable": 0.0})["variable"])
    df["Fixed Component (€/tx)"] = df["Card Type"].map(lambda x: HIDDEN_COSTS.get(x, {"fixed": 0.0})["fixed"])
    df["Interchange Fee (%)"] = df["Card Type"].map(lambda x: HIDDEN_COSTS.get(x, {"interchange": 0.0})["interchange"])

    # Total turnover per row = Transaction Amount * Number of Transactions
    df["Total Turnover (€)"] = df["Transaction Amount (€)"] * df["Number of Transactions"]

    # Formulas
    df["Collected Fee (€)"] = df["Total Turnover (€)"] * (df["Merchant Fee (%)"] / 100.0)

    df["Total Cost (€)"] = (
        (df["Total Turnover (€)"] * (df["Variable Component (%)"] / 100.0)) +
        (df["Number of Transactions"] * df["Fixed Component (€/tx)"]) +
        (df["Total Turnover (€)"] * (df["Interchange Fee (%)"] / 100.0))
    )

    df["Profit ICARD (€)"] = df["Collected Fee (€)"] - df["Total Cost (€)"]
    df["Agent Commission (€)"] = df["Profit ICARD (€)"] * 0.30

    # Aggregate by Card Type
    grouped_df = df.groupby("Card Type", as_index=False)[
        ["Total Turnover (€)", "Collected Fee (€)", "Agent Commission (€)"]
    ].sum()

    grouped_df["Merchant Fee (%)"] = grouped_df.apply(
        lambda r: (r["Collected Fee (€)"] / r["Total Turnover (€)"] * 100.0) if r["Total Turnover (€)"] > 0 else 0.0,
        axis=1
    )

    result_df = grouped_df[[
        "Card Type",
        "Total Turnover (€)",
        "Merchant Fee (%)",
        "Collected Fee (€)",
        "Agent Commission (€)"
    ]].rename(columns={"Collected Fee (€)": "Total Collected Fee (€)"})

    st.markdown("---")
    st.subheader("📈 Financial Results")

    st.dataframe(
        result_df,
        width="stretch",
        hide_index=True,
        column_config={
            "Total Turnover (€)": st.column_config.NumberColumn("Total Turnover (€)", format="%.2f"),
            "Merchant Fee (%)": st.column_config.NumberColumn("Merchant Fee (%)", format="%.2f"),
            "Total Collected Fee (€)": st.column_config.NumberColumn("Total Collected Fee (€)", format="%.2f"),
            "Agent Commission (€)": st.column_config.NumberColumn("Agent Commission (€)", format="%.2f"),
        }
    )

    total_volume = float(result_df["Total Turnover (€)"].sum())
    total_collected = float(result_df["Total Collected Fee (€)"].sum())
    total_agent_comm = float(result_df["Agent Commission (€)"].sum())

    st.markdown("---")
    st.subheader("📌 Simulation Summary")

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Volume", f"€{total_volume:,.2f}")
    col2.metric("Total Collected Fee", f"€{total_collected:,.2f}")
    col3.metric("Agent Commission", f"€{total_agent_comm:,.2f}")
