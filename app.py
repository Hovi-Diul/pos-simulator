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
    "Visa/Mastercard/Maestro - Debit (Domestic)": {
        "variable": 0.1010,    # %
        "fixed": 0.0116,       # EUR per transaction
        "interchange": 0.20    # %
    },
    "Visa/Mastercard/Maestro - Credit (Domestic)": {
        "variable": 0.1060,
        "fixed": 0.0116,
        "interchange": 0.30
    },
    "Visa/Mastercard/Maestro - Commercial (Domestic)": {
        "variable": 0.2422,
        "fixed": 0.0202,
        "interchange": 1.50
    },
    "Visa/Mastercard/Maestro - Debit (EEA)": {
        "variable": 0.1010,    # %
        "fixed": 0.0116,       # EUR per transaction
        "interchange": 0.20    # %
    },
    "Visa/Mastercard/Maestro - Credit (EEA)": {
        "variable": 0.1060,
        "fixed": 0.0116,
        "interchange": 0.30
    },
    "Visa/Mastercard/Maestro - Commercial (EEA)": {
        "variable": 0.2422,
        "fixed": 0.0202,
        "interchange": 1.50
    }
}

DOMESTIC_CARD_OPTIONS = [
    "Visa/Mastercard/Maestro - Debit (Domestic)",
    "Visa/Mastercard/Maestro - Credit (Domestic)",
    "Visa/Mastercard/Maestro - Commercial (Domestic)"
]

EEA_CARD_OPTIONS = [
    "Visa/Mastercard/Maestro - Debit (EEA)",
    "Visa/Mastercard/Maestro - Credit (EEA)",
    "Visa/Mastercard/Maestro - Commercial (EEA)"
]


def build_editor(title: str, description: str, default_rows: list, card_options: list, key: str):
    st.markdown("---")
    st.subheader(title)
    st.markdown(description)

    return st.data_editor(
        pd.DataFrame(default_rows),
        num_rows="dynamic",
        width="stretch",
        key=key,
        column_config={
            "Card Type": st.column_config.SelectboxColumn(
                "Card Type",
                options=card_options,
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


def process_section(edited_df: pd.DataFrame, default_card: str) -> pd.DataFrame:
    if edited_df is None or edited_df.empty:
        return pd.DataFrame()

    df = edited_df.copy()
    df["Card Type"] = df["Card Type"].fillna(default_card).astype(str)
    df["Transaction Amount (€)"] = pd.to_numeric(df["Transaction Amount (€)"], errors="coerce").fillna(0.0)
    df["Number of Transactions"] = pd.to_numeric(df["Number of Transactions"], errors="coerce").fillna(0.0)
    df["Merchant Fee (%)"] = pd.to_numeric(df["Merchant Fee (%)"], errors="coerce").fillna(0.0)

    df["Variable Component (%)"] = df["Card Type"].map(lambda x: HIDDEN_COSTS.get(x, {"variable": 0.0})["variable"])
    df["Fixed Component (€/tx)"] = df["Card Type"].map(lambda x: HIDDEN_COSTS.get(x, {"fixed": 0.0})["fixed"])
    df["Interchange Fee (%)"] = df["Card Type"].map(lambda x: HIDDEN_COSTS.get(x, {"interchange": 0.0})["interchange"])

    df["Total Turnover (€)"] = df["Transaction Amount (€)"] * df["Number of Transactions"]
    df["Collected Fee (€)"] = df["Total Turnover (€)"] * (df["Merchant Fee (%)"] / 100.0)

    df["Total Cost (€)"] = (
        (df["Total Turnover (€)"] * (df["Variable Component (%)"] / 100.0)) +
        (df["Number of Transactions"] * df["Fixed Component (€/tx)"]) +
        (df["Total Turnover (€)"] * (df["Interchange Fee (%)"] / 100.0))
    )

    df["Profit ICARD (€)"] = df["Collected Fee (€)"] - df["Total Cost (€)"]
    df["Agent Commission (€)"] = df["Profit ICARD (€)"] * 0.30

    grouped_df = df.groupby("Card Type", as_index=False)[
        ["Total Turnover (€)", "Collected Fee (€)", "Agent Commission (€)"]
    ].sum()

    grouped_df["Merchant Fee (%)"] = grouped_df.apply(
        lambda r: (r["Collected Fee (€)"] / r["Total Turnover (€)"] * 100.0) if r["Total Turnover (€)"] > 0 else 0.0,
        axis=1
    )

    return grouped_df[[
        "Card Type",
        "Total Turnover (€)",
        "Merchant Fee (%)",
        "Collected Fee (€)",
        "Agent Commission (€)"
    ]].rename(columns={"Collected Fee (€)": "Total Collected Fee (€)"})


domestic_defaults = [
    {
        "Card Type": "Visa/Mastercard/Maestro - Debit (Domestic)",
        "Transaction Amount (€)": 50.0,
        "Number of Transactions": 100,
        "Merchant Fee (%)": 1.10
    },
    {
        "Card Type": "Visa/Mastercard/Maestro - Credit (Domestic)",
        "Transaction Amount (€)": 50.0,
        "Number of Transactions": 100,
        "Merchant Fee (%)": 1.50
    },
    {
        "Card Type": "Visa/Mastercard/Maestro - Commercial (Domestic)",
        "Transaction Amount (€)": 50.0,
        "Number of Transactions": 100,
        "Merchant Fee (%)": 2.00
    }
]

eea_defaults = [
    {
        "Card Type": "Visa/Mastercard/Maestro - Debit (EEA)",
        "Transaction Amount (€)": 50.0,
        "Number of Transactions": 100,
        "Merchant Fee (%)": 1.10
    },
    {
        "Card Type": "Visa/Mastercard/Maestro - Credit (EEA)",
        "Transaction Amount (€)": 50.0,
        "Number of Transactions": 100,
        "Merchant Fee (%)": 1.50
    },
    {
        "Card Type": "Visa/Mastercard/Maestro - Commercial (EEA)",
        "Transaction Amount (€)": 50.0,
        "Number of Transactions": 100,
        "Merchant Fee (%)": 2.00
    }
]

edited_domestic = build_editor(
    title="Domestic Cards Scenario Input",
    description="Select a Domestic card type, enter the average transaction amount, number of transactions, and proposed Merchant Fee (%).",
    default_rows=domestic_defaults,
    card_options=DOMESTIC_CARD_OPTIONS,
    key="domestic_editor"
)

edited_eea = build_editor(
    title="EEA Cards Scenario Input",
    description="Select an EEA card type, enter the average transaction amount, number of transactions, and proposed Merchant Fee (%).",
    default_rows=eea_defaults,
    card_options=EEA_CARD_OPTIONS,
    key="eea_editor"
)

domestic_results = process_section(edited_domestic, DOMESTIC_CARD_OPTIONS[0])
eea_results = process_section(edited_eea, EEA_CARD_OPTIONS[0])

combined_results = pd.concat([df for df in [domestic_results, eea_results] if not df.empty], ignore_index=True)

if not combined_results.empty:
    st.markdown("---")
    st.subheader("Financial Results")

    st.dataframe(
        combined_results,
        width="stretch",
        hide_index=True,
        column_config={
            "Total Turnover (€)": st.column_config.NumberColumn("Total Turnover (€)", format="%.2f"),
            "Merchant Fee (%)": st.column_config.NumberColumn("Merchant Fee (%)", format="%.2f"),
            "Total Collected Fee (€)": st.column_config.NumberColumn("Total Collected Fee (€)", format="%.2f"),
            "Agent Commission (€)": st.column_config.NumberColumn("Agent Commission (€)", format="%.2f"),
        }
    )

    total_volume = float(combined_results["Total Turnover (€)"].sum())
    total_collected = float(combined_results["Total Collected Fee (€)"].sum())
    total_agent_comm = float(combined_results["Agent Commission (€)"].sum())

    st.markdown("---")
    st.subheader("Simulation Summary")

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Volume", f"€{total_volume:,.2f}")
    col2.metric("Total Collected Fee", f"€{total_collected:,.2f}")
    col3.metric("Agent Commission", f"€{total_agent_comm:,.2f}")
