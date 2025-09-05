import streamlit as st
import pandas as pd
import joblib
from data_store import load_expenses, add_expense, monthly_summary, category_breakdown

st.set_page_config(page_title="Personal Financial Tracker", page_icon="💰", layout="wide")

# Sidebar Navigation
page = st.sidebar.radio("Navigate", ["📊 Dashboard", "🤖 Predictions"])

# ---------------- Dashboard ----------------
if page == "📊 Dashboard":
    st.title("Personal Financial Tracker 💰")
    st.caption("Track, analyze, and export your daily expenses.")

    with st.form("add_expense_form", clear_on_submit=True):
        st.subheader("➕ Add Expense")
        col1, col2, col3 = st.columns(3)
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

    df = load_expenses()
    if df.empty:
        st.info("No expenses yet. Add some above!")
    else:
        st.subheader("All Expenses 💸")
        st.dataframe(df.sort_values("date", ascending=False), use_container_width=True, hide_index=True)

        # KPIs
        total_spend = df['amount'].sum()
        this_month = df[df["date"].dt.to_period('M') == pd.Timestamp("today").to_period("M")]
        this_month_spend = this_month["amount"].sum()
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Spend (all time)", f"₹ {total_spend:,.2f}")
        c2.metric("This Month", f"₹ {this_month_spend:,.2f}")
        c3.metric("Total Records", len(df))

        # Charts
        st.subheader("📊 Insights")
        colA, colB = st.columns(2)
        with colA:
            st.markdown("**Monthly Trend**")
            msum = monthly_summary(df)
            st.line_chart(msum, x="year_month", y="total_spend", height=280)
        with colB:
            st.markdown("**Category Breakdown**")
            csum = category_breakdown(df)
            st.bar_chart(csum, x="category", y="total_spend", height=280)

        # Export
        st.download_button(
            "⬇️ Download data (CSV)",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name="expenses.csv",
            mime="text/csv",
        )

# ---------------- Predictions ----------------
elif page == "🤖 Predictions":
    st.title("Expense Prediction 🤖")
    st.caption("Forecast next month's spending using ML model.")

    df = load_expenses()
    if df.empty:
        st.warning("Add some expenses first to train the model.")
    else:
        try:
            model = joblib.load("model.pkl")
            msum = monthly_summary(df)
            msum['year_month'] = pd.to_datetime(msum['year_month'])
            latest = msum.iloc[-1]

            # Create next month features
            next_month = latest['year_month'] + pd.DateOffset(months=1)
            features = {
                "month_num": next_month.month,
                "year": next_month.year,
                "lag_1": latest['total_spend'],
                "lag_2": msum.iloc[-2]['total_spend'] if len(msum) > 1 else latest['total_spend'],
                "lag_3": msum.iloc[-3]['total_spend'] if len(msum) > 2 else latest['total_spend'],
                "rolling_3": msum['total_spend'].tail(3).mean(),
                "rolling_6": msum['total_spend'].tail(6).mean(),
                "is_quarter_end": int(next_month.month % 3 == 0),
                "is_year_start": int(next_month.month == 1),
            }
            X_next = pd.DataFrame([features])
            pred = model.predict(X_next)[0]

            st.success(f"📅 Predicted spend for {next_month.strftime('%B %Y')}: ₹ {pred:,.2f}")

            # ---------------- Forecast Chart ----------------
            forecast_df = msum.copy()
            forecast_df = forecast_df[['year_month', 'total_spend']].rename(columns={'total_spend': 'actual'})
            forecast_df = forecast_df.set_index('year_month')

            # Add prediction
            forecast_df.loc[next_month] = [pred]

            st.subheader("📈 Forecast Visualization")
            st.line_chart(forecast_df, height=350)

        except Exception as e:
            st.error(f"Prediction failed: {e}")
