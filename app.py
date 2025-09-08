
import streamlit as st
import pandas as pd
import plotly.express as px

from auth import create_token
from data_store import (
    create_user, verify_user, add_expense,
    load_expenses, monthly_summary, category_breakdown
)
from train_model import train_model

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Personal Finance Tracker", page_icon="💰", layout="wide")



# ---------------- SESSION STATE ----------------
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "token" not in st.session_state:
    st.session_state.token = None

# ---------------- AUTH ----------------
st.title("💰 Personal Finance Tracker")

if not st.session_state.user_id:
    choice = st.radio("Login or Signup", ["Login", "Signup"], horizontal=True)

    if choice == "Signup":
        with st.form("signup_form"):
            username = st.text_input("👤 Username")
            password = st.text_input("🔑 Password", type="password")
            if st.form_submit_button("Create Account"):
                try:
                    _ = create_user(username, password)
                    st.success("✅ Account created! Please login.")
                except Exception as e:
                    st.error(str(e))
    else:  # Login
        with st.form("login_form"):
            username = st.text_input("👤 Username")
            password = st.text_input("🔑 Password", type="password")
            if st.form_submit_button("Login"):
                uid = verify_user(username, password)
                if uid:
                    token = create_token(uid)
                    st.session_state.user_id = uid
                    st.session_state.token = token
                    st.session_state.username = username
                    st.success("✅ Logged in successfully")
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials")

else:
    st.sidebar.success(f"Logged in as: {st.session_state.username}")
    if st.sidebar.button("🚪 Logout"):
        st.session_state.user_id = None
        st.session_state.token = None
        st.rerun()

    # ---------------- MAIN APP ----------------
    uid = st.session_state.user_id

    # Add Expense
    with st.form("add_expense_form", clear_on_submit=True):
        st.subheader("➕ Add Expense")
        col1, col2, col3 = st.columns(3)

        with col1: date = st.date_input("Date")
        with col2: category = st.selectbox("Category", ["Food","Transport","Bills","Shopping","Health","Entertainment","Rent","Other"])
        with col3: amount = st.number_input("Amount", min_value=0.0, step=0.5)
        notes = st.text_input("Notes (optional)")
        if st.form_submit_button("Add"):
            add_expense(uid, date, category, amount, notes)
            st.success("✅ Expense added!")

        with col1:
            date = st.date_input("Date")
        with col2:
            category = st.selectbox("Category", 
                        ["Food", "Transport", "Bills", "Shopping", "Health", "Entertainment", "Rent", "Other"])
        with col3:
            amount = st.number_input("Amount", min_value=0.0, step=0.5, format="%.2f")
        notes = st.text_input("Notes (Optional)", placeholder="e.g. , Lunch with friends")
        submitted = st.form_submit_button("Add")
        if submitted:
            try:
                add_expense(date, category, amount, notes)
                st.success("✅ Expense added")
            except Exception as e:
                st.error(f"Error: {e}")


    df = load_expenses(uid)
    if df.empty:
        st.info("No expenses yet")
    else:
        st.subheader("📊 Dashboard")

        # Ensure datetime & compute KPIs
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        now = pd.Timestamp.now()
        this_month_df = df[(df["date"].dt.year == now.year) & (df["date"].dt.month == now.month)]
        this_month_expense = float(this_month_df["amount"].sum())
        total = float(df["amount"].sum())
        last_dt = df["date"].max()
        last_str = last_dt.strftime("%Y-%m-%d") if pd.notna(last_dt) else "N/A"

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("💸 Total Spend", f"₹ {total:,.2f}")
        c2.metric("📆 This Month", f"₹ {this_month_expense:,.2f}")
        c3.metric("📝 Records", int(len(df)))
        c4.metric("🕒 Last Expense", last_str)

        st.dataframe(df.sort_values("date", ascending=False), use_container_width=True, hide_index=True)

        # Charts (Plotly, theme-aware)
        colA, colB = st.columns(2)
        with colA:
            msum = monthly_summary(uid)  # expects columns: year_month, total_spend
            fig1 = px.line(msum, x="year_month", y="total_spend", markers=True, title="Monthly Expense Trend")
            fig1.update_layout(margin=dict(l=20, r=20, t=50, b=20))
            st.plotly_chart(fig1, use_container_width=True)
        with colB:
            csum = category_breakdown(uid)  # expects columns: category, total_spend
            fig2 = px.bar(csum, x="category", y="total_spend", title="Category Breakdown")
            fig2.update_layout(margin=dict(l=20, r=20, t=50, b=20))
            st.plotly_chart(fig2, use_container_width=True)

        # ---- Prediction ----
        st.subheader("🔮 Predict Next Month's Expense")
        if st.button("📊 Train & Predict"):
            try:
                result = train_model(uid)
                model = result["model"]

                # Get monthly summary
                msum = monthly_summary(uid)
                msum["year_month"] = pd.to_datetime(msum["year_month"])

                # Build features for all months
                X = pd.DataFrame({
                    "month_num": msum["year_month"].dt.month,
                    "year": msum["year_month"].dt.year,
                    "lag_1": msum["total_spend"].shift(1),
                    "rolling_3": msum["total_spend"].rolling(3).mean()
                }).dropna()

                # Align target with features
                y = msum.loc[X.index, "total_spend"]

                # Predictions for all months
                preds = model.predict(X)

                # Create comparison DataFrame
                comparison_df = pd.DataFrame({
                    "Month": msum.loc[X.index, "year_month"].dt.strftime("%b %Y"),
                    "Actual": y.values,
                    "Predicted": preds
                })

                # Show table
                st.subheader("📊 Actual vs Predicted Expenses (Historical)")
                st.dataframe(comparison_df)

                # Plot Actual vs Predicted
                import plotly.graph_objects as go
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=comparison_df["Month"], y=comparison_df["Actual"],
                                        mode='lines+markers', name='Actual'))
                fig.add_trace(go.Scatter(x=comparison_df["Month"], y=comparison_df["Predicted"],
                                        mode='lines+markers', name='Predicted'))

                fig.update_layout(title="📊 Actual vs Predicted Monthly Expenses",
                                xaxis_title="Month",
                                yaxis_title="Expense (₹)",
                                template="plotly_white")

                st.plotly_chart(fig, use_container_width=True)

            except Exception as e:
                st.error(str(e))

