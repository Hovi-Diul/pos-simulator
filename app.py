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
        "variable": 0.1010,   # %
        "fixed": 0.0116,      # € на транзакция
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
st.subheader("📊 Въвеждане на сценарий от дистрибутора")
st.markdown("Изберете вид карта, въведете очаквания месечен обем, брой транзакции и предлаганата такса (Merchant Fee).")

# Начални данни за таблицата, които дистрибуторът вижда и може да редактира
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

# Изчисления с автоматично сливане със скритите вътрешни разходи
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

    st.markdown("---")
    st.subheader("📈 Финансови Резултати")

    # Подготвяме таблицата за показване (без Profit ICARD и Net Profit ICARD)
    result_df = df[[
        "Card Type", 
        "Transaction Amount (€)", 
        "Number of Transactions",
        "Merchant Fee (%)",
        "Collected Merchant Fee (€)", 
        "Agent Commission (30%) (€)"
    ]]

    # Преименуваме колоната за агента в таблицата, за да е по-удобна за четене
    result_df = result_df.rename(columns={"Agent Commission (30%) (€)": "Комисионна дистрибутор (€)"})

    # Форматираме само числените колони
    numeric_cols = [
        "Transaction Amount (€)", 
        "Merchant Fee (%)",
        "Collected Merchant Fee (€)", 
        "Комисионна дистрибутор (€)"
    ]
    
    st.dataframe(result_df.style.format("{:.2f}", subset=numeric_cols), use_container_width=True)

    # Обобщени KPI метрики в края на екрана (точно 3 колони: Общ Обем / Събрана Такса / Комисионна дистрибутор)
    total_volume = df["Transaction Amount (€)"].sum()
    total_collected = df["Collected Merchant Fee (€)"].sum()
    total_agent_comm = df["Agent Commission (30%) (€)"].sum()

    st.markdown("---")
    st.subheader("📌 Обобщение на симулацията")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Общ Обем", f"€{total_volume:,.2f}")
    col2.metric("Събрана Такса", f"€{total_collected:,.2f}")
    col3.metric("Комисионна дистрибутор", f"€{total_agent_comm:,.2f}")
