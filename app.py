import streamlit as st
import pandas as pd

st.set_page_config(page_title="ICARD POS Commission Simulator", layout="wide")

st.title("💳 POS Commission & Profit Simulator")
st.markdown("Интерактивен калкулатор за симулация на приходи и комисиони преди сключване на договор.")

# ==========================================
# СКРИТИ ВЪТРЕШНИ РАЗХОДИ НА ICARD (БЕКЕНД)
# Дистрибуторите не ги виждат и не могат да ги пипат!
# ==========================================
HIDDEN_COSTS = {
    "VS/MC/Maestro consumer debit": {
        "variable": 0.15,   # %
        "fixed": 0.05,      # € на транзакция
        "interchange": 0.70 # %
    },
    "VS/MC/Maestro consumer credit": {
        "variable": 0.20,
        "fixed": 0.05,
        "interchange": 1.10
    },
    "VS/MC/Maestro commercial": {
        "variable": 0.30,
        "fixed": 0.10,
        "interchange": 1.50
    }
}

st.markdown("---")
st.subheader("📊 Въвеждане на сценарий от дистрибутора")
st.markdown("Изберете вид карта, въведете очаквания месечен обем, брой транзакции и предлаганата такса (Merchant Fee).")

# Начални данни за таблицата, които дистрибуторът вижда и може да редактира (само обеми и такса към мерчанта)
default_user_data = pd.DataFrame([
    {
        "Card Type": "VS/MC/Maestro consumer debit",
        "Transaction Amount (€)": 50000.0,
        "Number of Transactions": 1000,
        "Merchant Fee (%)": 1.10
    },
    {
        "Card Type": "VS/MC/Maestro consumer credit",
        "Transaction Amount (€)": 20000.0,
        "Number of Transactions": 300,
        "Merchant Fee (%)": 1.50
    },
    {
        "Card Type": "VS/MC/Maestro commercial",
        "Transaction Amount (€)": 10000.0,
        "Number of Transactions": 100,
        "Merchant Fee (%)": 2.00
    }
])

# Таблицата, която дистрибуторът вижда и пипа
edited_df = st.data_editor(default_user_data, num_rows="dynamic", use_container_width=True)

# Изчисления с автоматично сливане със скътите вътрешни разходи
if not edited_df.empty:
    df = edited_df.copy()
    
    # Автоматично дръпване на скритите разходи според избрания вид карта
    df["Variable Component (%)"] = df["Card Type"].map(lambda x: HIDDEN_COSTS.get(x, {"variable": 0})["variable"])
    df["Fixed Component (€/tx)"] = df["Card Type"].map(lambda x: HIDDEN_COSTS.get(x, {"fixed": 0})["fixed"])
    df["Interchange Fee (%)"] = df["Card Type"].map(lambda x: HIDDEN_COSTS.get(x, {"interchange": 0})["interchange"])
    
    # Формули
    df["Collected Merchant Fee (€)"] = df["Transaction Amount (€)"] * (df["Merchant Fee (%)"] / 100)
    
    df["Total Cost (€)"] = (
        (df["Transaction Amount (€)"] * (df["Variable Component (%)"] / 100)) +
        (df["Number of Transactions"] * df["Fixed Component (€/tx)"]) +
        (df["Transaction Amount (€)"] * (df["Interchange Fee (%)"] / 100))
    )
    
    df["Profit ICARD (€)"] = df["Collected Merchant Fee (€)"] - df["Total Cost (€)"]
    df["Agent Commission (30%) (€)"] = df["Profit ICARD (€)"] * 0.30
    df["Net Profit ICARD (€)"] = df["Profit ICARD (€)"] - df["Agent Commission (30%) (€)"]

    st.markdown("---")
    st.subheader("📈 Финансови Резултати")

    # Показваме само чистите резултати към дистрибутора (без да разкриваме разходните компоненти)
    st.dataframe(df[[
        "Card Type", 
        "Transaction Amount (€)", 
        "Number of Transactions",
        "Merchant Fee (%)",
        "Collected Merchant Fee (€)", 
        "Profit ICARD (€)", 
        "Agent Commission (30%) (€)", 
        "Net Profit ICARD (€)"
    ]].style.format("{:.2f}"))

    # Обобщени KPI метрики в горната част
    total_volume = df["Transaction Amount (€)"].sum()
    total_collected = df["Collected Merchant Fee (€)"].sum()
    total_icard_profit = df["Profit ICARD (€)"].sum()
    total_agent_comm = df["Agent Commission (30%) (€)"].sum()
    total_net_profit = df["Net Profit ICARD (€)"].sum()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Общ Обем", f"€{total_volume:,.2f}")
    col2.metric("Събрана Такса", f"€{total_collected:,.2f}")
    col3.metric("ICARD Бруто Приход", f"€{total_icard_profit:,.2f}")
    col4.metric("ICARD Нетна Печалба", f"€{total_net_profit:,.2f}")