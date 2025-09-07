import streamlit as st
import pandas as pd
import joblib
from auth import create_token, verify_token
from data_store import create_user, verify_user, add_expense, load_expenses, monthly_summary, category_breakdown
from train_model import train_model

st.set_page_config(page_title="Personal Finance Tracker", page_icon="💰", layout="wide")

# ---- SESSION STATE ----
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "token" not in st.session_state:
    st.session_state.token = None

# ---- AUTH ----
st.title("💰 Personal Finance Tracker")

if not st.session_state.user_id:
    choice = st.radio("Login or Signup", ["Login", "Signup"])

    if choice == "Signup":
        with st.form("signup_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Create Account")
            if submitted:
                try:
                    uid = create_user(username, password)
                    st.success("✅ Account created! Please login.")
                except Exception as e:
                    st.error(str(e))

    else:  # Login
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")
            if submitted:
                uid = verify_user(username, password)
                if uid:
                    token = create_token(uid)
                    st.session_state.user_id = uid
                    st.session_state.token = token
                    st.success("✅ Logged in successfully")
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials")

else:
    st.sidebar.success("Logged in")
    if st.sidebar.button("Logout"):
        st.session_state.user_id = None
        st.session_state.token = None
        st.rerun()

    # ---- MAIN APP ----
    uid = st.session_state.user_id

    with st.form("add_expense_form", clear_on_submit=True):
        st.subheader("➕ Add Expense")
        col1, col2, col3 = st.columns(3)
        with col1: date = st.date_input("Date")
        with col2: category = st.selectbox("Category", ["Food","Transport","Bills","Shopping","Health","Entertainment","Rent","Other"])
        with col3: amount = st.number_input("Amount", min_value=0.0, step=0.5)
        notes = st.text_input("Notes (optional)")
        if st.form_submit_button("Add"):
            add_expense(uid, date, category, amount, notes)
            st.success("Expense added!")

    df = load_expenses(uid)
    if df.empty:
        st.info("No expenses yet")
    else:
        st.subheader("📊 Dashboard")
        total = df["amount"].sum()
        c1,c2,c3 = st.columns(3)
        c1.metric("Total Spend", f"₹{total:,.2f}")
        c2.metric("Records", len(df))
        c3.metric("Last expense", str(df["date"].max().date()))

        st.dataframe(df.sort_values("date", ascending=False), use_container_width=True, hide_index=True)

        colA, colB = st.columns(2)
        with colA:
            st.line_chart(monthly_summary(uid), x="year_month", y="total_spend")
        with colB:
            st.bar_chart(category_breakdown(uid), x="category", y="total_spend")

        # ---- Prediction ----
        st.subheader("🔮 Predict Next Month's Expense")
        if st.button("Train & Predict"):
            try:
                result = train_model(uid)
                model = result["model"]
                msum = monthly_summary(uid)
                latest = pd.to_datetime(msum["year_month"]).max()
                next_month = (latest + pd.offsets.MonthBegin(1))
                features = pd.DataFrame({
                    "month_num": [next_month.month],
                    "year": [next_month.year],
                    "lag_1": [msum["total_spend"].iloc[-1]],
                    "rolling_3": [msum["total_spend"].tail(3).mean()]
                })
                pred = model.predict(features)[0]
                st.success(f"📈 Predicted expense for {next_month.strftime('%B %Y')}: ₹{pred:,.2f}")
            except Exception as e:
                st.error(str(e))
