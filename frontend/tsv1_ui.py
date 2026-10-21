"""Streamlit frontend dashboard for Trade Store V1."""
import datetime
import os
import requests
import streamlit as st

BASE_URL = os.getenv(
    "API_BASE_URL",
    "https://tsv1-bxcxcthgbadyc3ht.malaysiawest-01.azurewebsites.net"
)

st.set_page_config(
    page_title="Trade Store Dashboard",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Trade Store Management Dashboard (TSV1)")
st.markdown("View stored trades, insert new trade records, or trigger business operations.")

st.markdown("""
<style>
    /* Fix title cropping */
    h1 {
        white-space: nowrap;
        overflow: visible;
        font-size: clamp(1.2rem, 2.5vw, 2rem) !important;
        line-height: 1.3 !important;
        padding-bottom: 0.3rem;
    }
    /* Top-level tabs — larger */
    .stTabs [data-baseweb="tab-list"] { gap: 16px; }
    .stTabs [data-baseweb="tab"] {
        font-size: 2.8rem;
        font-weight: 900;
        padding: 24px 80px;
        letter-spacing: 0.05em;
        height: auto;
        overflow: visible;
        white-space: nowrap;
    }

    /* Radio buttons (sub-sections) — compact */
    div[role="radiogroup"] label {
        font-size: 0.72rem;
        padding: 1px 6px;
    }

    /* Reduce vertical spacing throughout */
    .block-container { padding-top: 0.5rem; padding-bottom: 0.5rem; }
    div[data-testid="stVerticalBlock"] > div { gap: 0.2rem; }
</style>
""", unsafe_allow_html=True)

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

# ── Top-level Tabs ─────────────────────────────────────────────────────────────
tab_tsv1, tab_anomaly = st.tabs(["📈 TSV1", "🚨 Anomaly"])

# ══ TSV1 Tab ══════════════════════════════════════════════════════════════════
with tab_tsv1:
    tsv1_section = st.radio(
        "Select Section",
        ["📋 View Trades", "➕ Insert / Update Trade", "🔍 Get Trade by ID"],
        horizontal=True,
        key="tsv1_radio"
    )
    st.divider()

    # ── View Trades ────────────────────────────────────────────────────────────
    if tsv1_section == "📋 View Trades":
        st.subheader("All Trades in Database")
        try:
            resp = requests.get(f"{BASE_URL}/trades")
            if resp.status_code == 200:
                trades = resp.json()
                if trades:
                    st.dataframe(trades, use_container_width=True, height=248)
                    st.info(f"Total Trades: {len(trades)}")
                else:
                    st.warning("No trades found in the store.")
            else:
                st.error(f"Failed to fetch trades: {resp.status_code}")
        except requests.exceptions.ConnectionError:
            st.error("⚠️ Cannot connect to the backend API.")

    # ── Insert / Update Trade ──────────────────────────────────────────────────
    elif tsv1_section == "➕ Insert / Update Trade":
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

    # ── Get Trade by ID ────────────────────────────────────────────────────────
    elif tsv1_section == "🔍 Get Trade by ID":
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

    # ── Documentation placeholder ──────────────────────────────────────────────
    st.divider()
    # Documentation section coming soon

# ══ Anomaly Tab ════════════════════════════════════════════════════════════════
with tab_anomaly:
    anomaly_section = st.radio(
        "Select Section",
        ["🔍 View Anomalies", "✅ Submit Review", "📜 View All Reviews"],
        horizontal=True,
        key="anomaly_radio"
    )
    st.divider()

    # ── View Anomalies ─────────────────────────────────────────────────────────
    if anomaly_section == "🔍 View Anomalies":
        st.subheader("Flagged Trades")
        st.markdown("Trades flagged as **UNUSUAL** by the anomaly detection model.")
        if st.button("Run Anomaly Scan"):
            try:
                resp = requests.get(f"{BASE_URL}/anomalies")
                if resp.status_code == 200:
                    data = resp.json()
                    col1, col2 = st.columns(2)
                    col1.metric("Total Trades Scanned", data["total_trades_scanned"])
                    col2.metric("Unusual Trades Found", data["unusual_trades_count"])
                    if data["anomalies"]:
                        st.dataframe(data["anomalies"], use_container_width=True, height=248)
                    else:
                        st.success("✅ No anomalies detected.")
                else:
                    st.error(f"Error {resp.status_code}: {resp.text}")
            except Exception as e:
                st.error(f"Failed to connect: {e}")

    # ── Submit Review ──────────────────────────────────────────────────────────
    elif anomaly_section == "✅ Submit Review":
        st.subheader("Submit Human Review")
        st.markdown("Mark a flagged trade as **SAFE** or **UNSAFE** after human review.")
        with st.form("review_form"):
            col1, col2 = st.columns(2)
            with col1:
                review_trade_id = st.text_input("Trade ID *", placeholder="e.g. TRD001")
                review_version  = st.number_input("Version *", min_value=1, value=1, step=1)
            with col2:
                review_category = st.selectbox("Category", ["UNSEEN_COUNTERPARTY", "ISOLATION_FOREST"])
                review_status   = st.selectbox("Review Status", ["SAFE", "UNSAFE"])
            review_reason = st.text_area("Reason *", placeholder="Explain why this trade is SAFE or UNSAFE")
            review_submitted = st.form_submit_button("Submit Review")

        if review_submitted:
            if not review_trade_id or not review_reason:
                st.error("Please fill in all required fields.")
            else:
                payload = {
                    "version":       int(review_version),
                    "category":      review_category,
                    "review_status": review_status,
                    "reason":        review_reason.strip(),
                }
                try:
                    resp = requests.post(
                        f"{BASE_URL}/anomalies/{review_trade_id.strip()}/review",
                        json=payload
                    )
                    if resp.status_code == 200:
                        st.success(f"✅ Review submitted for trade '{review_trade_id}'.")
                        st.json(resp.json())
                    elif resp.status_code == 404:
                        st.warning("Trade not found.")
                    else:
                        detail = resp.json().get("detail", resp.text)
                        st.error(f"❌ Error ({resp.status_code}): {detail}")
                except Exception as e:
                    st.error(f"Failed to connect: {e}")

    # ── View All Reviews ───────────────────────────────────────────────────────
    elif anomaly_section == "📜 View All Reviews":
        st.subheader("All Submitted Reviews")
        st.markdown("All human reviews submitted for anomalous trades.")
        try:
            resp = requests.get(f"{BASE_URL}/anomalies/reviews")
            if resp.status_code == 200:
                data = resp.json()
                st.metric("Total Reviews", data["total_reviews"])
                if data["reviews"]:
                    st.dataframe(data["reviews"], use_container_width=True, height=248)
                else:
                    st.info("No reviews submitted yet.")
            else:
                st.error(f"Error {resp.status_code}: {resp.text}")
        except Exception as e:
            st.error(f"Failed to connect: {e}")

    # ── Documentation placeholder ──────────────────────────────────────────────
    st.divider()
    # Documentation section coming soon
