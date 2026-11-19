import json
import streamlit as st
import pandas as pd

st.set_page_config(page_title="ICARD POS Commission Simulator", layout="wide")

st.title("POS Commission & Profit Simulator")
st.markdown("Interactive calculator for simulating revenues, costs, and commissions.")

# ==========================================
# BASE INTERNAL ICARD COSTS (INITIAL DEFAULTS)
# Distributors cannot see or modify these without internal password.
# ==========================================
BASE_HIDDEN_COSTS = {
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
        "variable": 0.2422,    # %
        "fixed": 0.0148,       # EUR per transaction
        "interchange": 0.20    # %
    },
    "Visa/Mastercard/Maestro - Credit (EEA)": {
        "variable": 0.2422,
        "fixed": 0.02019,
        "interchange": 0.30
    },
    "Visa/Mastercard/Maestro - Commercial (EEA)": {
        "variable": 0.2422,
        "fixed": 0.0202,
        "interchange": 1.50
    },
    "All cards (International)": {
        "variable": 0.8405,    # %
        "fixed": 0.2260,       # EUR per transaction
        "interchange": 1.50    # %
    }
}

INTERNAL_PASSWORD = st.secrets.get("INTERNAL_PASSWORD", "ICARD_INTERNAL_2026")

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

INTERNATIONAL_CARD_OPTIONS = [
    "All cards (International)"
]


def costs_dict_to_df(costs_dict: dict) -> pd.DataFrame:
    return pd.DataFrame([
        {
            "Card Type": card,
            "Variable (%)": float(vals["variable"]),
            "Fixed (€/tx)": float(vals["fixed"]),
            "Interchange (%)": float(vals["interchange"])
        }
        for card, vals in costs_dict.items()
    ])


def df_to_costs_dict(df: pd.DataFrame, fallback: dict) -> dict:
    updated = {k: dict(v) for k, v in fallback.items()}
    if df is None or df.empty:
        return updated

    for _, row in df.iterrows():
        card = str(row.get("Card Type", "")).strip()
        if card:
            updated[card] = {
                "variable": float(pd.to_numeric(row.get("Variable (%)"), errors="coerce") or 0.0),
                "fixed": float(pd.to_numeric(row.get("Fixed (€/tx)"), errors="coerce") or 0.0),
                "interchange": float(pd.to_numeric(row.get("Interchange (%)"), errors="coerce") or 0.0),
            }
    return updated


def get_default_domestic() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "Card Type": "Visa/Mastercard/Maestro - Debit (Domestic)",
            "Transaction Amount (€)": 50.0,
            "Number of Transactions": 100,
            "Merchant Fee (%)": 0.95
        },
        {
            "Card Type": "Visa/Mastercard/Maestro - Credit (Domestic)",
            "Transaction Amount (€)": 75.0,
            "Number of Transactions": 80,
            "Merchant Fee (%)": 1.20
        },
        {
            "Card Type": "Visa/Mastercard/Maestro - Commercial (Domestic)",
            "Transaction Amount (€)": 100.0,
            "Number of Transactions": 40,
            "Merchant Fee (%)": 2.60
        }
    ])


def get_default_eea() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "Card Type": "Visa/Mastercard/Maestro - Debit (EEA)",
            "Transaction Amount (€)": 50.0,
            "Number of Transactions": 100,
            "Merchant Fee (%)": 1.10
        },
        {
            "Card Type": "Visa/Mastercard/Maestro - Credit (EEA)",
            "Transaction Amount (€)": 90.0,
            "Number of Transactions": 50,
            "Merchant Fee (%)": 1.60
        },
        {
            "Card Type": "Visa/Mastercard/Maestro - Commercial (EEA)",
            "Transaction Amount (€)": 90.0,
            "Number of Transactions": 35,
            "Merchant Fee (%)": 2.60
        }
    ])


def get_default_international() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "Card Type": "All cards (International)",
            "Transaction Amount (€)": 50.0,
            "Number of Transactions": 100,
            "Merchant Fee (%)": 3.00
        }
    ])


if "reset_counter" not in st.session_state:
    st.session_state.reset_counter = 0

if "costs_reset_counter" not in st.session_state:
    st.session_state.costs_reset_counter = 0

if "saved_default_costs" not in st.session_state:
    st.session_state.saved_default_costs = {k: dict(v) for k, v in BASE_HIDDEN_COSTS.items()}

if "active_costs" not in st.session_state:
    st.session_state.active_costs = {k: dict(v) for k, v in BASE_HIDDEN_COSTS.items()}

if "domestic_data" not in st.session_state:
    st.session_state.domestic_data = get_default_domestic()

if "eea_data" not in st.session_state:
    st.session_state.eea_data = get_default_eea()

if "international_data" not in st.session_state:
    st.session_state.international_data = get_default_international()

if "internal_unlocked" not in st.session_state:
    st.session_state.internal_unlocked = False

if "costs_saved_message" not in st.session_state:
    st.session_state.costs_saved_message = ""

# Reset button for distributor scenario tables
if st.button("Reset to Defaults"):
    st.session_state.domestic_data = get_default_domestic()
    st.session_state.eea_data = get_default_eea()
    st.session_state.international_data = get_default_international()
    st.session_state.reset_counter += 1
    st.rerun()


def build_editor(title: str, description: str, data_df: pd.DataFrame, card_options: list, key_prefix: str):
    st.markdown("---")
    st.subheader(title)
    st.markdown(description)

    return st.data_editor(
        data_df,
        num_rows="dynamic",
        width="stretch",
        key=f"{key_prefix}_{st.session_state.reset_counter}",
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


def calculate_section(edited_df: pd.DataFrame, default_card: str, costs_map: dict) -> pd.DataFrame:
    if edited_df is None or edited_df.empty:
        return pd.DataFrame()

    df = edited_df.copy()
    df["Card Type"] = df["Card Type"].fillna(default_card).astype(str)
    df["Transaction Amount (€)"] = pd.to_numeric(df["Transaction Amount (€)"], errors="coerce").fillna(0.0)
    df["Number of Transactions"] = pd.to_numeric(df["Number of Transactions"], errors="coerce").fillna(0.0)
    df["Merchant Fee (%)"] = pd.to_numeric(df["Merchant Fee (%)"], errors="coerce").fillna(0.0)

    df["Variable Component (%)"] = df["Card Type"].map(lambda x: costs_map.get(x, {"variable": 0.0})["variable"])
    df["Fixed Component (€/tx)"] = df["Card Type"].map(lambda x: costs_map.get(x, {"fixed": 0.0})["fixed"])
    df["Interchange Fee (%)"] = df["Card Type"].map(lambda x: costs_map.get(x, {"interchange": 0.0})["interchange"])

    df["Total Turnover (€)"] = df["Transaction Amount (€)"] * df["Number of Transactions"]
    df["Collected Fee (€)"] = df["Total Turnover (€)"] * (df["Merchant Fee (%)"] / 100.0)

    df["Total Cost (€)"] = (
        (df["Total Turnover (€)"] * (df["Variable Component (%)"] / 100.0)) +
        (df["Number of Transactions"] * df["Fixed Component (€/tx)"]) +
        (df["Total Turnover (€)"] * (df["Interchange Fee (%)"] / 100.0))
    )

    df["Profit ICARD (€)"] = df["Collected Fee (€)"] - df["Total Cost (€)"]
    # When ICARD is at a loss (Profit < 0), distributor commission is 0.0
    df["Agent Commission (€)"] = (df["Profit ICARD (€)"] * 0.30).clip(lower=0.0)

    grouped_df = df.groupby("Card Type", as_index=False)[
        [
            "Total Turnover (€)",
            "Collected Fee (€)",
            "Total Cost (€)",
            "Profit ICARD (€)",
            "Agent Commission (€)"
        ]
    ].sum()

    grouped_df["Merchant Fee (%)"] = grouped_df.apply(
        lambda r: (r["Collected Fee (€)"] / r["Total Turnover (€)"] * 100.0) if r["Total Turnover (€)"] > 0 else 0.0,
        axis=1
    )

    return grouped_df


edited_domestic = build_editor(
    title="Domestic Cards",
    description="Select a Domestic card type, enter the average transaction amount, number of transactions, and proposed Merchant Fee (%).",
    data_df=st.session_state.domestic_data,
    card_options=DOMESTIC_CARD_OPTIONS,
    key_prefix="domestic_editor"
)

edited_eea = build_editor(
    title="EEA Cards",
    description="Select an EEA card type, enter the average transaction amount, number of transactions, and proposed Merchant Fee (%).",
    data_df=st.session_state.eea_data,
    card_options=EEA_CARD_OPTIONS,
    key_prefix="eea_editor"
)

edited_international = build_editor(
    title="International Cards",
    description="Enter the average transaction amount, number of transactions, and proposed Merchant Fee (%) for International cards.",
    data_df=st.session_state.international_data,
    card_options=INTERNATIONAL_CARD_OPTIONS,
    key_prefix="international_editor"
)

# ==========================================
# INTERNAL ICARD SECTION (PASSWORD PROTECTED)
# ==========================================
st.markdown("---")
st.subheader("Internal ICARD Parameters & Profit")

entered_password = st.text_input(
    "Internal access password",
    type="password",
    key="internal_password_input"
)

if entered_password:
    if entered_password == INTERNAL_PASSWORD:
        st.session_state.internal_unlocked = True
    else:
        st.session_state.internal_unlocked = False
        st.error("Invalid password.")

if st.session_state.internal_unlocked:
    st.markdown("#### Cost Parameters by Card & Region (Editable)")
    st.caption("Any change updates calculations immediately. Click 'Save as Default' to store updated values as the default for this session.")

    edited_costs_df = st.data_editor(
        costs_dict_to_df(st.session_state.active_costs),
        num_rows="fixed",
        width="stretch",
        key=f"internal_costs_editor_{st.session_state.costs_reset_counter}",
        column_config={
            "Card Type": st.column_config.TextColumn("Card Type", disabled=True),
            "Variable (%)": st.column_config.NumberColumn(
                "Variable (%)",
                min_value=0.0,
                step=0.001,
                format="%.4f"
            ),
            "Fixed (€/tx)": st.column_config.NumberColumn(
                "Fixed (€/tx)",
                min_value=0.0,
                step=0.0001,
                format="%.5f"
            ),
            "Interchange (%)": st.column_config.NumberColumn(
                "Interchange (%)",
                min_value=0.0,
                step=0.01,
                format="%.2f"
            ),
        }
    )

    # Apply live edits immediately to active_costs
    live_costs = df_to_costs_dict(edited_costs_df, st.session_state.active_costs)
    st.session_state.active_costs = live_costs

    btn_col1, btn_col2 = st.columns([1, 1])
    with btn_col1:
        if st.button("Save as Default"):
            st.session_state.saved_default_costs = {k: dict(v) for k, v in live_costs.items()}
            st.session_state.costs_saved_message = "Saved current parameters as default for this session."
    with btn_col2:
        if st.button("Restore Saved Default"):
            st.session_state.active_costs = {k: dict(v) for k, v in st.session_state.saved_default_costs.items()}
            st.session_state.costs_reset_counter += 1
            st.session_state.costs_saved_message = "Restored saved default parameters."
            st.rerun()

    if st.session_state.costs_saved_message:
        st.success(st.session_state.costs_saved_message)

    with st.expander("Export updated defaults for permanent code update"):
        st.download_button(
            label="Download Parameters (JSON)",
            data=json.dumps(st.session_state.saved_default_costs, indent=2),
            file_name="icard_hidden_costs.json",
            mime="application/json"
        )
        st.code(f"BASE_HIDDEN_COSTS = {json.dumps(st.session_state.saved_default_costs, indent=4)}", language="python")

active_costs_map = st.session_state.active_costs

domestic_full = calculate_section(edited_domestic, DOMESTIC_CARD_OPTIONS[0], active_costs_map)
eea_full = calculate_section(edited_eea, EEA_CARD_OPTIONS[0], active_costs_map)
international_full = calculate_section(edited_international, INTERNATIONAL_CARD_OPTIONS[0], active_costs_map)

combined_full = pd.concat(
    [df for df in [domestic_full, eea_full, international_full] if not df.empty],
    ignore_index=True
)

if not combined_full.empty:
    distributor_results = combined_full[[
        "Card Type",
        "Total Turnover (€)",
        "Merchant Fee (%)",
        "Collected Fee (€)",
        "Agent Commission (€)"
    ]].rename(columns={"Collected Fee (€)": "Total Collected Fee (€)"})

    st.markdown("---")
    st.subheader("Financial Results")

    st.dataframe(
        distributor_results,
        width="stretch",
        hide_index=True,
        column_config={
            "Total Turnover (€)": st.column_config.NumberColumn("Total Turnover (€)", format="%.2f"),
            "Merchant Fee (%)": st.column_config.NumberColumn("Merchant Fee (%)", format="%.2f"),
            "Total Collected Fee (€)": st.column_config.NumberColumn("Total Collected Fee (€)", format="%.2f"),
            "Agent Commission (€)": st.column_config.NumberColumn("Agent Commission (€)", format="%.2f"),
        }
    )

    total_volume = float(distributor_results["Total Turnover (€)"].sum())
    total_collected = float(distributor_results["Total Collected Fee (€)"].sum())
    total_agent_comm = float(distributor_results["Agent Commission (€)"].sum())

    st.markdown("---")
    st.subheader("Simulation Summary")

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Volume", f"€{total_volume:,.2f}")
    col2.metric("Total Collected Fee", f"€{total_collected:,.2f}")
    col3.metric("Agent Commission", f"€{total_agent_comm:,.2f}")

if st.session_state.internal_unlocked and not combined_full.empty:
    internal_breakdown = combined_full[[
        "Card Type",
        "Total Turnover (€)",
        "Collected Fee (€)",
        "Total Cost (€)",
        "Profit ICARD (€)",
        "Agent Commission (€)"
    ]]

    st.markdown("#### Profit & Cost Breakdown by Card & Region")
    st.dataframe(
        internal_breakdown,
        width="stretch",
        hide_index=True,
        column_config={
            "Total Turnover (€)": st.column_config.NumberColumn("Total Turnover (€)", format="%.2f"),
            "Collected Fee (€)": st.column_config.NumberColumn("Collected Fee (€)", format="%.2f"),
            "Total Cost (€)": st.column_config.NumberColumn("Total Cost (€)", format="%.2f"),
            "Profit ICARD (€)": st.column_config.NumberColumn("Profit ICARD (€)", format="%.2f"),
            "Agent Commission (€)": st.column_config.NumberColumn("Agent Commission (€)", format="%.2f"),
        }
    )

    total_cost = float(combined_full["Total Cost (€)"].sum())
    total_icard_profit = float(combined_full["Profit ICARD (€)"].sum())
    total_comm = float(combined_full["Agent Commission (€)"].sum())

    m1, m2, m3 = st.columns(3)
    m1.metric("Total ICARD Cost", f"€{total_cost:,.2f}")
    m2.metric("ICARD Profit (Gross)", f"€{total_icard_profit:,.2f}")
    m3.metric("Agent Commission", f"€{total_comm:,.2f}")
