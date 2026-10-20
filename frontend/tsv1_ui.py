"""Streamlit frontend dashboard for Trade Store V1."""
import datetime
import requests
import streamlit as st

BASE_URL = "https://tsv1-bxcxcthgbadyc3ht.malaysiawest-01.azurewebsites.net"

st.set_page_config(
    page_title="Trade Store Dashboard",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Trade Store Management Dashboard")
st.markdown("View stored trades, insert new trade records, or trigger business operations.")

# ── Sidebar ────────────────────────────────────────────────────────────────────
st.sidebar.header("Operations & Actions")

if st.sidebar.button("🔄 Refresh Data"):
    st.rerun()

if st.sidebar.button("⏰ Run Expiry Scan"):
    try:
        resp = requests.post(f"{BASE_URL}/trades/expire")
        if resp.status_code == 200:
            data = resp.json()
            st.sidebar.success(data.get("message"))
            st.sidebar.metric("Trades Marked Expired", data.get("trades_marked_expired", 0))
        else:
            st.sidebar.error(f"Error {resp.status_code}: {resp.text}")
    except Exception as e:
        st.sidebar.error(f"Failed to connect to API: {e}")

st.sidebar.markdown("---")
st.sidebar.markdown(f"**Backend API:** `{BASE_URL}`")

# ── Tabs ───────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📋 View Trades", "➕ Insert / Update Trade", "🔍 Get Trade by ID"])

# Tab 1: View Trades
with tab1:
    st.subheader("All Trades in Database")
    try:
        resp = requests.get(f"{BASE_URL}/trades")
        if resp.status_code == 200:
            trades = resp.json()
            if trades:
                st.dataframe(trades, use_container_width=True)
                st.info(f"Total Trades: {len(trades)}")
            else:
                st.warning("No trades found in the store.")
        else:
            st.error(f"Failed to fetch trades: {resp.status_code}")
    except requests.exceptions.ConnectionError:
        st.error("⚠️ Cannot connect to the backend API.")

# Tab 2: Insert / Update Trade
with tab2:
    st.subheader("Insert or Update Trade Record")
    with st.form("trade_form"):
        col1, col2 = st.columns(2)
        with col1:
            trade_id        = st.text_input("Trade ID *", value="TRD001")
            version         = st.number_input("Version *", min_value=1, value=1, step=1)
            counterparty_id = st.text_input("Counterparty ID *", value="CP001")
        with col2:
            portfolio_id  = st.text_input("Portfolio ID *", value="PF001")
            maturity_date = st.date_input("Maturity Date *", value=datetime.date.today() + datetime.timedelta(days=30))
            created_date  = st.date_input("Created Date", value=datetime.date.today())

        submitted = st.form_submit_button("Submit Trade")
        if submitted:
            payload = {
                "trade_id":        trade_id.strip(),
                "version":         int(version),
                "counterparty_id": counterparty_id.strip(),
                "portfolio_id":    portfolio_id.strip(),
                "maturity_date":   maturity_date.strftime("%d/%m/%Y"),
                "created_date":    created_date.strftime("%d/%m/%Y"),
                "expired":         "N",
            }
            try:
                resp = requests.post(f"{BASE_URL}/trades", json=payload)
                if resp.status_code == 200:
                    st.success(f"✅ Trade '{trade_id}' saved successfully!")
                    st.json(resp.json())
                else:
                    detail = resp.json().get("detail", resp.text)
                    st.error(f"❌ Error ({resp.status_code}): {detail}")
            except Exception as e:
                st.error(f"Failed to submit trade: {e}")

# Tab 3: Get Trade by ID
with tab3:
    st.subheader("Get Trade by ID")
    search_id = st.text_input("Enter Trade ID", placeholder="e.g. TRD001")
    if st.button("Search"):
        if search_id:
            try:
                resp = requests.get(f"{BASE_URL}/trades/{search_id.strip()}")
                if resp.status_code == 200:
                    st.json(resp.json())
                elif resp.status_code == 404:
                    st.warning("Trade not found.")
                else:
                    st.error(f"Error {resp.status_code}: {resp.text}")
            except Exception as e:
                st.error(f"Failed to connect: {e}")
        else:
            st.warning("Please enter a Trade ID.")
