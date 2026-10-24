"""Streamlit frontend dashboard for Trade Store V1."""
import datetime
import os

import requests
import streamlit as st

# ── Config ─────────────────────────────────────────────────────────────────────
BASE_URL = os.getenv(
    "API_BASE_URL",
    "https://tsv1-bxcxcthgbadyc3ht.malaysiawest-01.azurewebsites.net"
)

# Absolute path to the docs/diagrams/ folder (works regardless of cwd)
_FRONTEND_DIR = os.path.dirname(os.path.abspath(__file__))
_DOCS_DIR     = os.path.join(_FRONTEND_DIR, "..", "docs")
_DIAG_DIR     = os.path.join(_DOCS_DIR, "diagrams")

st.set_page_config(
    page_title="Trade Store Dashboard",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Trade Store Management Dashboard (TSV1)")
st.markdown("View stored trades, insert new trade records, or trigger business operations.")

st.markdown("""
<style>
    h1 {
        white-space: nowrap;
        overflow: visible;
        font-size: clamp(1.2rem, 2.5vw, 2rem) !important;
        line-height: 1.3 !important;
        padding-bottom: 0.3rem;
        margin-top: 1.5rem !important;
    }
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
    div[role="radiogroup"] label {
        font-size: 0.72rem;
        padding: 1px 6px;
    }
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
tab_tsv1, tab_anomaly, tab_future = st.tabs(["📈 TSV1  ","  🚨 Anomaly  ","  🔭 Future Scope  "])


# ══ TSV1 Tab ══════════════════════════════════════════════════════════════════
with tab_tsv1:

    # ── Section selector (operations only) ────────────────────────────────────
    tsv1_section = st.radio(
        "Select Section",
        [
            "📋 View Trades",
            "➕ Insert / Update Trade",
            "🔍 Get Trade by ID",
            "🗑️ Delete Trade",
        ],
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
                maturity_date = st.date_input(
                    "Maturity Date *",
                    value=datetime.date.today() + datetime.timedelta(days=30)
                )
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

    # ── Delete Trade ───────────────────────────────────────────────────────────
    elif tsv1_section == "🗑️ Delete Trade":
        st.subheader("Delete Trade")
        delete_id = st.text_input("Enter Trade ID to delete", placeholder="e.g. TRD001")
        if st.button("Delete"):
            if not delete_id.strip():
                st.warning("Please enter a Trade ID.")
            else:
                try:
                    resp = requests.delete(f"{BASE_URL}/trades/{delete_id.strip()}")
                    if resp.status_code == 200:
                        st.success("✅ Trade deleted successfully.")
                        st.json(resp.json())
                    elif resp.status_code == 404:
                        st.warning("Trade not found.")
                    else:
                        detail = resp.json().get("detail", resp.text) if resp.headers.get("content-type", "").startswith("application/json") else resp.text
                        st.error(f"❌ Error ({resp.status_code}): {detail}")
                except Exception as e:
                    st.error(f"Failed to connect: {e}")

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

    # ══════════════════════════════════════════════════════════════════════════
    # DOCUMENTATION — collapsible sections, all closed by default
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown("---")

    # helper: render diagram PNG at a fixed pixel width (centred via columns)
    def show_diagram(filename: str, caption: str, width_px: int = 680):
        # Load the pre-generated PNG (SVG cannot be displayed by st.image directly)
        png_file = filename.replace(".svg", ".png")
        path = os.path.join(_DIAG_DIR, png_file)
        if not os.path.exists(path):
            st.warning(f"Diagram not found: `{png_file}`")
            return
        st.image(path, caption=caption, width=width_px)

    # ── 1. Solution Overview ──────────────────────────────────────────────────
    with st.expander("1 · Solution Overview", expanded=False):
        st.markdown(
            "**Trade Store V1 (TSV1)** is a RESTful API built with **FastAPI** that acts "
            "as a central, validated, versioned trade repository. It accepts trades from "
            "upstream systems, enforces business rules, persists them in SQLite, and "
            "exposes a unified read API for downstream consumers."
        )
        show_diagram("02_solution_overview.svg", "Solution Overview", width_px=830)

    # ── 2. High Level Design ──────────────────────────────────────────────────
    with st.expander("2 · High Level Design", expanded=False):
        st.markdown(
            "Streamlit frontend talks to a **FastAPI** backend on Azure App Service. "
            "The API layer validates requests via Pydantic, applies business rules in "
            "`services.py`, and persists data in SQLite. A GitHub Actions pipeline runs "
            "tests, a Trivy security scan, and deploys to Azure on every push to `main`."
        )
        show_diagram("03_high_level_design.svg", "High Level Design", width_px=830)

    # ── 3. Low Level Design ───────────────────────────────────────────────────
    with st.expander("3 · Low Level Design", expanded=False):
        st.markdown(
            "How all five modules inside `app/` interact — routing, validation, "
            "business logic, data model, and the database layer. All DB calls are "
            "wrapped in `try/finally` to guarantee `connection.close()`."
        )
        show_diagram("09_low_level_design.svg", "Low Level Design", width_px=830)


    # ── 5. Class / Data Model ─────────────────────────────────────────────────
    with st.expander("4 · Class / Data Model", expanded=False):
        st.markdown(
            "Two Pydantic models (`TradeRequest`, `TradeResponse`), a dataclass (`Trade`), "
            "and the service/database modules that orchestrate all operations."
        )
        show_diagram("04_class_data_model.svg", "Class / Data Model", width_px=660)

    # ── 6. Database Schema ────────────────────────────────────────────────────
    with st.expander("5 · Database Schema", expanded=False):
        st.markdown(
            "The `trades` table is the core store. `anomaly_reviews` holds the human "
            "review audit trail. An index on `maturity_date` speeds up the expiry scan."
        )
        show_diagram("10_database_schema.svg", "Database Schema", width_px=620)
        st.code(
            """CREATE TABLE trades (
    trade_id        TEXT    PRIMARY KEY,
    version         INTEGER NOT NULL CHECK(version >= 1),
    counterparty_id TEXT    NOT NULL,
    portfolio_id    TEXT    NOT NULL,
    maturity_date   TEXT    NOT NULL,
    created_date    TEXT    NOT NULL,
    expired         TEXT    NOT NULL DEFAULT 'N'
);
CREATE INDEX idx_trades_maturity ON trades (maturity_date);""",
            language="sql"
        )

    # ── 7. DB Atomicity ───────────────────────────────────────────────────────
    with st.expander("6 · Sequence Diagram — POST /trades", expanded=False):
        st.markdown(
            "Full request lifecycle: Pydantic validates the schema (→ 422), "
            "`services.py` checks date rules and version guard (→ 400), then "
            "executes an atomic `INSERT … ON CONFLICT DO UPDATE` (→ 200)."
        )
        show_diagram("05_seq_post_trade.svg", "Sequence -- POST /trades", width_px=780)

    with st.expander("7 · Database Atomicity & Transactions", expanded=False):
        st.markdown(
            "Every write to SQLite goes through an explicit **commit / rollback** cycle. "
            "The upsert uses `INSERT … ON CONFLICT(trade_id) DO UPDATE SET …` — a single "
            "atomic statement that either fully succeeds or fully rolls back, preventing "
            "partial or duplicate writes."
        )
        show_diagram("13_db_atomicity.svg", "DB Atomicity", width_px=680)

    # ── 8. CI/CD Pipeline ─────────────────────────────────────────────────────
    with st.expander("8 · CI/CD Pipeline", expanded=False):
        st.markdown(
            "Every push or PR to `main` triggers **pytest** → **Trivy** CVE scan → "
            "**Azure App Service** deploy (Malaysia West)."
        )
        show_diagram("12_cicd_pipeline.svg", "CI/CD Pipeline", width_px=730)
        st.info(
            "**Live URL:** "
            "https://tsv1-bxcxcthgbadyc3ht.malaysiawest-01.azurewebsites.net"
        )


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
                review_category = st.selectbox("Category", ["UNUSUAL_COUNTERPARTY_PORTFOLIO"])
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

    st.divider()

    # ── Anomaly Documentation ─────────────────────────────────────────────────
    with st.expander("1 · What We Detect & Why", expanded=False):
        st.markdown(
            "**Goal:** Identify trades whose counterparty-portfolio relationships look "
            "suspicious compared to historically normal trading patterns.\n\n"
            "We detect **three categories** of anomalies:"
        )
        col1, col2, col3 = st.columns(3)
        col1.error(
            "**🔴 New Counterparty**\n\n"
            "The counterparty ID has never appeared in the 2,000 training trades. "
            "A brand-new counterparty with no history is an immediate red flag."
        )
        col2.warning(
            "**🟠 Unseen CP–Portfolio Pair**\n\n"
            "The counterparty exists in training data, but this specific "
            "counterparty + portfolio combination has never been seen together before."
        )
        col3.info(
            "**🔵 Isolation Forest Outlier**\n\n"
            "The trade's frequency profile (how often this CP, portfolio, and pair "
            "appear) is statistically unusual compared to normal trades — caught by "
            "the ML model even when both CP and pair are known."
        )
        st.markdown(
            "---\n"
            "**Features used for detection** (all three computed per trade):\n"
            "- `counterparty_frequency` — how many times this CP appeared in training\n"
            "- `portfolio_frequency` — how many times this portfolio appeared in training\n"
            "- `pair_frequency` — how many times this exact CP + portfolio pair appeared\n\n"
            "A `log1p` transform is applied to reduce the effect of high-frequency outliers "
            "before feeding into the model."
        )
        show_diagram("14_anomaly_overview.svg", "Anomaly Detection — Solution Overview", width_px=830)

    with st.expander("2 · ML Training Pipeline", expanded=False):
        st.markdown(
            "Offline training reads **2,000 synthetic normal trades**, computes frequency maps "
            "for counterparties, portfolios, and CP-portfolio pairs, applies a `log1p` transform, "
            "then trains an **IsolationForest** (200 estimators, 3% contamination). "
            "The model + all three frequency maps are saved together into `relationship_model.pkl` "
            "and loaded once at API startup."
        )
        show_diagram("15_anomaly_ml_pipeline.svg", "ML Training Pipeline", width_px=560)

    with st.expander("3 · Detection Decision Logic", expanded=False):
        st.markdown(
            "For each trade, three checks run **in priority order**. "
            "The first one that fires sets the reason. If none fire, the trade is **NORMAL**.\n\n"
            "1. Is the counterparty completely new? → `UNUSUAL` (New counterparty detected)\n"
            "2. Is the CP-portfolio pair unseen? → `UNUSUAL` (Pair not seen in training)\n"
            "3. Does IsolationForest score it as -1? → `UNUSUAL` (Unusual pattern)\n"
            "4. None of the above → `NORMAL`"
        )
        show_diagram("16_anomaly_detection_logic.svg", "Detection Logic", width_px=560)
        show_diagram("17_anomaly_sequence.svg", "GET /anomalies Sequence", width_px=760)


# ══ Future Scope Tab ══════════════════════════════════════════════════════════
with tab_future:
    st.subheader("Future Scope — Scalability Roadmap")
    st.markdown(
        "Planned architectural improvements to scale Trade Store V1 beyond its current "
        "single-instance setup for production-grade, high-throughput environments."
    )
    st.divider()

    # ── 1. API Scaling ─────────────────────────────────────────────────────
    with st.expander("1 · API Scaling — Horizontal Scale-Out", expanded=False):
        st.markdown(
            "**Problem:** A single FastAPI instance becomes a bottleneck under high request volume.\n\n"
            "**Solution:** Run multiple stateless FastAPI instances behind a **Load Balancer**. "
            "Each instance is identical and shares a single database. The load balancer distributes "
            "incoming HTTP/HTTPS requests across healthy instances and removes failed ones automatically."
        )
        show_diagram("API_Scaling.png", "API Scaling — Horizontal Scale-Out", width_px=640)
        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Key Design Points**")
            st.markdown(
                "- All API instances are **stateless** — no session state stored in memory\n"
                "- Load balancer performs **health checks** and routes only to healthy instances\n"
                "- **Auto-scaling** adds/removes instances based on CPU or request-rate thresholds\n"
                "- Zero-downtime deploys: roll instances one at a time"
            )
        with c2:
            st.markdown("**Tools**")
            st.markdown(
                "- Load Balancer: **Azure App Service** auto-scale or **NGINX**\n"
                "- Container orchestration: **Azure Container Apps**\n"
                "- Monitoring: **Azure Monitor**, **Dynatrace**"
            )

    # ── 2. Additional Anomalies ────────────────────────────────────────────
    with st.expander("2 · Additional Anomaly Detectors", expanded=False):
        st.markdown(
            "**Problem:** The current detector only flags unusual counterparty-portfolio relationships. "
            "Other suspicious trade patterns (e.g. unusual maturity dates) go undetected.\n\n"
            "**Solution:** Extend the anomaly detection service with additional detectors running in parallel, "
            "each specialising in a different dimension of trade data."
        )
        show_diagram("Additinal_anomalies.png", "Additional Anomaly Detectors", width_px=640)
        st.markdown("---")
        c1, c2, c3 = st.columns(3)
        c1.info(
            "**Unusual CP–Portfolio Relationship**\n\n"
            "Detects uncommon counterparty-portfolio combinations based on historical patterns. "
            "Already implemented — extended with scoring."
        )
        c2.warning(
            "**Unusual Maturity-Date Patterns**\n\n"
            "Finds trades with maturity periods that are statistical outliers "
            "compared to the normal distribution of maturities in the store."
        )
        c3.success(
            "**Existing Isolation Forest Detector**\n\n"
            "Extended to use additional features (maturity days, version frequency) "
            "beyond the current counterparty/portfolio frequency features."
        )

    # ── 3. DB Scaling ─────────────────────────────────────────────────────
    with st.expander("3 · DB Scaling — Read / Write Split", expanded=False):
        st.markdown(
            "**Problem:** A single database handles all reads and writes. Under high load, "
            "read-heavy operations (GET /trades, anomaly scans) compete with writes (POST /trades).\n\n"
            "**Solution:** Introduce a **Primary + Read Replica** topology. The FastAPI layer routes "
            "write requests (POST/PUT) to the Primary and read requests (GET) to the Read Replica, "
            "each holding an identical clone of the data via replication."
        )
        show_diagram("DB_Scaling.png", "DB Scaling — Read / Write Split", width_px=900)
        st.markdown("---")
        st.markdown("**Routing in `database.py`**")
        st.markdown(
            "- `POST /trades` → **Write Service** → Primary Database\n"
            "- `GET /trades`, `GET /trades/{id}` → **Read Service** → Read Replica\n"
            "- Version check before upsert always queries **Primary** to avoid stale reads"
        )
