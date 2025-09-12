import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime


from auth import create_token  
from data_store import (
    create_user, verify_user, add_expense,
    load_expenses, monthly_summary, category_breakdown
)
from train_model import train_model


st.set_page_config(page_title="Personal Finance Tracker", page_icon="💰", layout="wide")


if "user_id" not in st.session_state:
    st.session_state["user_id"] = None
if "username" not in st.session_state:
    st.session_state["username"] = None
if "just_logged_in" not in st.session_state:
    st.session_state["just_logged_in"] = False


if st.session_state["just_logged_in"]:
    st.session_state["just_logged_in"] = False

    st.rerun()


st.title("💰 Personal Finance Tracker")


if not st.session_state["user_id"]:
    choice = st.radio("Login or Signup", ["Login", "Signup"], horizontal=True)

    if choice == "Signup":
        with st.form("signup_form", clear_on_submit=True):
            su_username = st.text_input("👤 Username")
            su_password = st.text_input("🔑 Password", type="password")
            if st.form_submit_button("Create Account"):
                try:
                    create_user(su_username, su_password)
                    st.success("✅ Account created! Please login.")
                except Exception as e:
                    st.error(f"Error creating account: {e}")

    else:  
        with st.form("login_form", clear_on_submit=True):
            li_username = st.text_input("👤 Username")
            li_password = st.text_input("🔑 Password", type="password")
            submitted = st.form_submit_button("Login")
            if submitted:
                try:
                    uid = verify_user(li_username, li_password)
                    if uid:
                        st.session_state["user_id"] = uid
                        st.session_state["username"] = li_username
                        
                        st.session_state["just_logged_in"] = True
                        st.success("✅ Logged in successfully — loading dashboard...")
                        st.rerun()
                    else:
                        st.error("❌ Invalid credentials")
                except Exception as e:
                    st.error(f"Login error: {e}")


else:
   
    st.sidebar.success(f"Logged in as: {st.session_state['username']}")
    if st.sidebar.button("🚪 Logout"):
        st.session_state["user_id"] = None
        st.session_state["username"] = None
        st.rerun()

   
    st.subheader("Welcome to your Dashboard")

    uid = st.session_state["user_id"]

    
    with st.form("add_expense_form", clear_on_submit=True):
        st.subheader("➕ Add Expense")
        col1, col2, col3 = st.columns(3)

        with col1:
            date_val = st.date_input("Date")
        with col2:
            category = st.selectbox("Category",
                                    ["Food", "Transport", "Bills", "Shopping", "Health", "Entertainment", "Rent", "Other"])
        with col3:
            amount = st.number_input("Amount", min_value=0.0, step=0.5, format="%.2f")

        notes = st.text_input("Notes (Optional)", placeholder="e.g. Lunch with friends")
        submitted = st.form_submit_button("Add")
        if submitted:
            try:
                
                if not isinstance(date_val, datetime):
                    date_dt = datetime.combine(date_val, datetime.min.time())
                else:
                    date_dt = date_val

                add_expense(uid, date_dt, category, amount, notes)
                st.success("✅ Expense added")
            except Exception as e:
                st.error(f"Error: {e}")

    
    try:
        df = load_expenses(uid)
    except Exception as e:
        st.error(f"Error loading expenses: {e}")
        df = pd.DataFrame(columns=["date", "category", "amount", "notes"])

    if df.empty:
        st.info("No expenses yet. Add your first expense above!")
    else:
        st.subheader("📊 Dashboard")

       
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

        
        colA, colB = st.columns(2)
        with colA:
            try:
                msum = monthly_summary(uid)
            except Exception as e:
                st.error(f"Error computing monthly summary: {e}")
                msum = pd.DataFrame()

            if not msum.empty:
                
                msum["year_month"] = pd.to_datetime(msum["year_month"])
                fig1 = px.line(msum, x="year_month", y="total_spend", markers=True, title="Monthly Expense Trend")
                fig1.update_layout(margin=dict(l=20, r=20, t=50, b=20))
                st.plotly_chart(fig1, use_container_width=True)

        with colB:
            try:
                csum = category_breakdown(uid)
            except Exception as e:
                st.error(f"Error computing category breakdown: {e}")
                csum = pd.DataFrame()

            if not csum.empty:
                fig2 = px.bar(csum, x="category", y="total_spend", title="Category Breakdown")
                fig2.update_layout(margin=dict(l=20, r=20, t=50, b=20))
                st.plotly_chart(fig2, use_container_width=True)

        
        st.subheader("🔮 Predict Next Month's Expense")
        if st.button("📊 Train & Predict"):
            try:
                result = train_model(uid)
                model = result.get("model") if isinstance(result, dict) else result

                
                msum = monthly_summary(uid)
                if msum.empty or len(msum) < 4:
                    st.warning("Not enough monthly history to train/predict (need at least 4 months).")
                else:
                    msum["year_month"] = pd.to_datetime(msum["year_month"])
                    X = pd.DataFrame({
                        "month_num": msum["year_month"].dt.month,
                        "year": msum["year_month"].dt.year,
                        "lag_1": msum["total_spend"].shift(1),
                        "rolling_3": msum["total_spend"].rolling(3).mean()
                    }).dropna()

                    y = msum.loc[X.index, "total_spend"]
                    preds = model.predict(X)

                    comparison_df = pd.DataFrame({
                        "Month": msum.loc[X.index, "year_month"].dt.strftime("%b %Y"),
                        "Actual": y.values,
                        "Predicted": preds
                    })

                    st.subheader("📊 Actual vs Predicted Expenses (Historical)")
                    st.dataframe(comparison_df, use_container_width=True)

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

                    
                    latest = msum["year_month"].max()
                    next_month = latest + pd.offsets.MonthBegin(1)
                    features = pd.DataFrame({
                        "month_num": [next_month.month],
                        "year": [next_month.year],
                        "lag_1": [msum["total_spend"].iloc[-1]],
                        "rolling_3": [msum["total_spend"].tail(3).mean()]
                    })
                    future_pred = model.predict(features)[0]
                    st.success(f"📈 Predicted expense for {next_month.strftime('%B %Y')}: ₹{future_pred:,.2f}")

            except Exception as e:
                st.error(f"Prediction error: {e}")
