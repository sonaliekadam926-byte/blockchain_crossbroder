import hashlib
import html
import json
from datetime import datetime, timezone

import streamlit as st

st.set_page_config(page_title="Cross-Border Settlement Ledger", layout="wide")

# Illustrative rate only. This app does not move real money.
DEMO_INR_PER_USD = 83.0
GENESIS_PREV = "0" * 64


# ----------------------------------------------------------------------------
# Ledger logic
# ----------------------------------------------------------------------------
def sha256(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def block_hash(index, timestamp, transaction, previous_hash):
    payload = {
        "index": index,
        "timestamp": timestamp,
        "transaction": transaction,
        "previous_hash": previous_hash,
    }
    return sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")))


def make_genesis():
    timestamp = datetime.now(timezone.utc).isoformat()
    tx = {"type": "GENESIS", "message": "Start of demo ledger"}
    return {
        "index": 0,
        "timestamp": timestamp,
        "transaction": tx,
        "previous_hash": GENESIS_PREV,
        "hash": block_hash(0, timestamp, tx, GENESIS_PREV),
    }


def add_block(chain, tx):
    index = len(chain)
    timestamp = datetime.now(timezone.utc).isoformat()
    previous_hash = chain[-1]["hash"]
    chain.append({
        "index": index,
        "timestamp": timestamp,
        "transaction": tx,
        "previous_hash": previous_hash,
        "hash": block_hash(index, timestamp, tx, previous_hash),
    })


def verify(chain):
    if not chain:
        return False, "The chain is empty."
    for i, block in enumerate(chain):
        expected = block_hash(block["index"], block["timestamp"],
                              block["transaction"], block["previous_hash"])
        if expected != block["hash"]:
            return False, f"Block #{i} data/hash mismatch. Data may have been changed."
        if i == 0:
            if block["previous_hash"] != GENESIS_PREV:
                return False, "Genesis block previous hash is invalid."
        elif block["previous_hash"] != chain[i - 1]["hash"]:
            return False, f"Block #{i} does not link to the previous block."
    return True, "All block hashes and links are valid."


def block_flags(chain):
    """Per-block integrity flag, used to colour the chain view."""
    flags = []
    for i, b in enumerate(chain):
        ok = block_hash(b["index"], b["timestamp"], b["transaction"], b["previous_hash"]) == b["hash"]
        if i > 0 and b["previous_hash"] != chain[i - 1]["hash"]:
            ok = False
        flags.append(ok)
    return flags


def short(h, n=8):
    return f"{h[:n]}…{h[-n:]}"


def fmt_time(iso):
    return datetime.fromisoformat(iso).strftime("%d %b %Y, %H:%M:%S UTC")


if "chain" not in st.session_state:
    st.session_state.chain = [make_genesis()]

# ----------------------------------------------------------------------------
# Styling
# ----------------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
:root {
  --navy:#0F2747; --navy2:#12315F; --accent:#1F5FBF; --ink:#18222F; --muted:#64748B;
  --line:#E2E8F0; --bg:#F3F5F8; --ok:#14693A; --okbg:#E6F4EC; --bad:#A11D1D; --badbg:#FCE8E8;
}
html, body, [class*="css"], .stApp {font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', sans-serif;}
#MainMenu, footer, header[data-testid="stHeader"], [data-testid="stToolbar"] {visibility:hidden; height:0;}
.block-container {padding: 0 1.5rem 1rem 1.5rem !important; max-width: 1180px !important;}

/* top bar */
.topbar {background: var(--navy); color:#fff; border-bottom: 3px solid var(--accent);
          width:100vw; margin-left: calc(50% - 50vw); margin-top:0;}
.topbar .in {max-width:1180px; margin:0 auto; padding: .9rem 1.5rem; display:flex; align-items:center; justify-content:space-between;}
.brand {display:flex; align-items:center; gap:.75rem; font-weight:600; letter-spacing:.01em;}
.mark {width:30px; height:30px; border-radius:7px; background: linear-gradient(135deg,#3B82F6,#1F5FBF);
       display:flex; align-items:center; justify-content:center; font-size:.8rem; font-weight:700;}
.brand small {display:block; font-weight:400; opacity:.65; font-size:.72rem; letter-spacing:.08em; text-transform:uppercase;}
.pill {border:1px solid rgba(255,255,255,.3); border-radius:999px; padding:.22rem .75rem; font-size:.72rem;
       letter-spacing:.06em; text-transform:uppercase; opacity:.9;}

/* page head */
.head {padding: 1.8rem 0 1.1rem 0;}
.head h1 {font-size:1.7rem; font-weight:650; color:var(--ink); margin:0; padding:0; letter-spacing:-.01em;}
.head p {color:var(--muted); margin:.35rem 0 0 0; font-size:.95rem; max-width: 760px;}
.notice {display:flex; gap:.7rem; align-items:flex-start; background:#fff; border:1px solid var(--line);
         border-left:4px solid #D69E2E; border-radius:8px; padding:.7rem 1rem; font-size:.84rem; color:#44505F; margin-bottom:1.3rem;}
.notice b {color: var(--ink);}

/* tabs */
.stTabs [data-baseweb="tab-list"] {gap: 1.6rem; border-bottom: 1px solid var(--line);}
.stTabs [data-baseweb="tab"] {padding: .6rem 0; font-weight:500; color: var(--muted);}
.stTabs [aria-selected="true"] {color: var(--navy2) !important; font-weight:600;}
.stTabs [data-baseweb="tab-highlight"] {background: var(--navy2); height: 2px;}
.stTabs [data-baseweb="tab-panel"] {padding-top: 1.3rem;}

/* cards */
div[data-testid="stVerticalBlockBorderWrapper"] {background:#fff; border-radius:10px; border:1px solid var(--line);
    box-shadow: 0 1px 2px rgba(15,39,71,.04);}
.ct {font-size:.72rem; font-weight:600; letter-spacing:.1em; text-transform:uppercase; color:var(--muted); margin-bottom:.9rem;}
label p {font-size:.8rem !important; font-weight:500 !important; color:#334155 !important;}
.stTextInput input, .stNumberInput input {font-size:.95rem;}
button[kind="primary"] {background: var(--navy2); border:none; font-weight:600; letter-spacing:.01em; padding:.6rem 1rem;}
button[kind="primary"]:hover {background: var(--accent);}
button[kind="secondary"] {border-color: var(--line); font-weight:500;}

/* summary */
.sum-row {display:flex; justify-content:space-between; padding:.62rem 0; border-bottom:1px solid var(--line); font-size:.9rem;}
.sum-row span:first-child {color:var(--muted);}
.sum-row span:last-child {font-weight:600; font-variant-numeric: tabular-nums;}
.sum-total {display:flex; justify-content:space-between; align-items:baseline; padding:.9rem 0 .2rem 0;}
.sum-total span:first-child {font-size:.85rem; color:var(--muted);}
.sum-total span:last-child {font-size:1.7rem; font-weight:650; color:var(--navy2); font-variant-numeric: tabular-nums;}
.route {display:flex; align-items:center; gap:.5rem; margin-bottom:.9rem; font-size:.82rem; font-weight:600; color:var(--navy2);}
.route .n {background:#EAF0FA; border:1px solid #D3DFF3; padding:.3rem .65rem; border-radius:6px;}
.route .a {color:#94A3B8;}
.fine {color:var(--muted); font-size:.76rem; margin-top:.5rem; line-height:1.45;}

/* kpis */
.kpis {display:grid; grid-template-columns: repeat(4, 1fr); gap:1rem; margin-bottom:1rem;}
.kpi {background:#fff; border:1px solid var(--line); border-radius:10px; padding:.9rem 1.1rem; box-shadow:0 1px 2px rgba(15,39,71,.04);}
.kpi .l {font-size:.72rem; color:var(--muted); letter-spacing:.08em; text-transform:uppercase; font-weight:600;}
.kpi .v {font-size:1.45rem; font-weight:650; margin-top:.2rem; font-variant-numeric: tabular-nums; color:var(--ink);}
.kpi .v.ok {color: var(--ok);} .kpi .v.bad {color: var(--bad);}
.integrity {border-radius:10px; padding:.8rem 1.1rem; margin-bottom:1.2rem; font-size:.9rem; display:flex; gap:.7rem; align-items:center;}
.integrity.ok {background: var(--okbg); color: var(--ok); border:1px solid #BFE3CD;}
.integrity.bad {background: var(--badbg); color: var(--bad); border:1px solid #F2BDBD;}
.integrity b {font-weight:650;}
.dot {width:9px; height:9px; border-radius:50%; background: currentColor; flex:none;}

/* chain */
.chain {display:flex; gap:0; overflow-x:auto; padding:.2rem .1rem 1rem .1rem; align-items:stretch;}
.cb {min-width:200px; background:#fff; border:1px solid var(--line); border-top:3px solid var(--navy2); border-radius:8px; padding:.7rem .8rem;
     font-size:.78rem; box-shadow:0 1px 2px rgba(15,39,71,.04);}
.cb.bad {border-top-color: var(--bad); background:#FFF8F8;}
.cb .t {font-weight:650; color:var(--ink); font-size:.82rem; margin-bottom:.35rem; display:flex; justify-content:space-between;}
.cb .t em {font-style:normal; font-weight:500; color:var(--muted); font-size:.7rem;}
.cb .k {color:var(--muted); font-size:.66rem; text-transform:uppercase; letter-spacing:.08em; margin-top:.4rem;}
.cb code {font-family:'JetBrains Mono', ui-monospace, Consolas, monospace; font-size:.72rem; color:#334155; background:none; padding:0;}
.link {display:flex; align-items:center; color:#94A3B8; padding:0 .35rem; font-size:1rem;}

.sec {font-size:.72rem; font-weight:600; letter-spacing:.1em; text-transform:uppercase; color:var(--muted); margin:1.3rem 0 .6rem 0;}
div[data-testid="stExpander"] {background:#fff; border:1px solid var(--line); border-radius:8px;}
.foot {color:#94A3B8; font-size:.76rem; text-align:center; padding:2rem 0 1.5rem 0;}
@media (max-width: 800px){ .kpis {grid-template-columns: repeat(2, 1fr);} }
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# Header
# ----------------------------------------------------------------------------
st.markdown("""
<div class="topbar"><div class="in">
  <div class="brand"><div class="mark">CB</div>
    <div>Cross-Border Settlement Ledger<small>Blockchain payment simulation</small></div></div>
  <div class="pill">Demo environment</div>
</div></div>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="head">
  <h1>India to USA transfer, recorded on a hash-linked ledger</h1>
  <p>Create a payment record, then inspect how each block is sealed with a SHA-256 hash and linked to the block before it.</p>
</div>
<div class="notice"><div><b>Demonstration only.</b> No funds are moved. The rate is fixed at
&#8377;{DEMO_INR_PER_USD:.2f} per USD and is not live. The ledger runs on a single computer and is not a distributed
blockchain or a payment service.</div></div>
""", unsafe_allow_html=True)


# ----------------------------------------------------------------------------
# Body
# ----------------------------------------------------------------------------
if True:
    payment_tab, ledger_tab = st.tabs(["New transfer", "Ledger"])

    with payment_tab:
        form_col, sum_col = st.columns([3, 2], gap="large")
        with form_col:
            with st.container(border=True):
                st.markdown('<div class="ct">Transfer details</div>', unsafe_allow_html=True)
                n1, n2 = st.columns(2)
                sender = n1.text_input("Sender name (India)", "Aarav")
                receiver = n2.text_input("Recipient name (USA)", "Emma")
                amount = st.number_input("Amount to send (INR)", min_value=1.0, max_value=10000000.0,
                                         value=10000.0, step=500.0, format="%.2f")
                usd = amount / DEMO_INR_PER_USD
                submit = st.button("Record transfer on ledger", type="primary", use_container_width=True)
                if submit:
                    if not sender.strip() or not receiver.strip():
                        st.error("Enter both sender and recipient names.")
                    elif sender.strip().casefold() == receiver.strip().casefold():
                        st.error("Sender and recipient must be different.")
                    else:
                        tx = {
                            "type": "CROSS_BORDER_PAYMENT",
                            "sender": sender.strip(),
                            "sender_country": "India",
                            "receiver": receiver.strip(),
                            "receiver_country": "USA",
                            "amount_inr": round(float(amount), 2),
                            "demo_rate_inr_per_usd": DEMO_INR_PER_USD,
                            "estimated_amount_usd": round(float(usd), 2),
                            "note": "Illustrative payment record; no funds transferred.",
                        }
                        add_block(st.session_state.chain, tx)
                        st.success(f"Transfer recorded in Block #{len(st.session_state.chain) - 1}. "
                                   "Open the Ledger tab to inspect it.")
        with sum_col:
            with st.container(border=True):
                st.markdown('<div class="ct">Transfer summary</div>', unsafe_allow_html=True)
                st.markdown(f"""
<div class="route"><span class="n">India &middot; INR</span><span class="a">&rarr;</span>
<span class="n">Ledger</span><span class="a">&rarr;</span><span class="n">USA &middot; USD</span></div>
<div class="sum-row"><span>You send</span><span>&#8377;{amount:,.2f}</span></div>
<div class="sum-row"><span>Demo exchange rate</span><span>&#8377;{DEMO_INR_PER_USD:,.2f} / USD</span></div>
<div class="sum-row"><span>Fees</span><span>Not modelled</span></div>
<div class="sum-total"><span>Recipient receives (est.)</span><span>${usd:,.2f}</span></div>
<div class="fine">Estimate excludes fees, taxes and live market movement. For demonstration purposes only.</div>
""", unsafe_allow_html=True)

    with ledger_tab:
        chain = st.session_state.chain
        payments = [b for b in chain if b["transaction"].get("type") == "CROSS_BORDER_PAYMENT"]
        valid, message = verify(chain)
        flags = block_flags(chain)
        total_inr = sum(b["transaction"]["amount_inr"] for b in payments)
        st.markdown(f"""
<div class="kpis">
  <div class="kpi"><div class="l">Blocks</div><div class="v">{len(chain)}</div></div>
  <div class="kpi"><div class="l">Payments</div><div class="v">{len(payments)}</div></div>
  <div class="kpi"><div class="l">Total value</div><div class="v">&#8377;{total_inr:,.2f}</div></div>
  <div class="kpi"><div class="l">Integrity</div><div class="v {'ok' if valid else 'bad'}">{'Verified' if valid else 'Compromised'}</div></div>
</div>
<div class="integrity {'ok' if valid else 'bad'}"><span class="dot"></span>
<span><b>{'Verification passed.' if valid else 'Verification failed.'}</b> {html.escape(message)}</span></div>
""", unsafe_allow_html=True)

        # chain strip
        st.markdown('<div class="sec">Chain overview</div>', unsafe_allow_html=True)
        parts = []
        for b, ok in zip(chain, flags):
            kind = "Genesis" if b["transaction"].get("type") == "GENESIS" else "Payment"
            parts.append(
                f'<div class="cb {"" if ok else "bad"}"><div class="t">Block #{b["index"]}<em>{kind}</em></div>'
                f'<div class="k">Hash</div><code>{short(b["hash"], 6)}</code>'
                f'<div class="k">Previous</div><code>{short(b["previous_hash"], 6)}</code></div>'
            )
        st.markdown('<div class="chain">' + '<div class="link">&rarr;</div>'.join(parts) + '</div>',
                    unsafe_allow_html=True)

        # transactions table
        st.markdown('<div class="sec">Transactions</div>', unsafe_allow_html=True)
        if payments:
            rows = [{
                "Block": f"#{b['index']}",
                "Time (UTC)": fmt_time(b["timestamp"]),
                "Sender": b["transaction"]["sender"],
                "Recipient": b["transaction"]["receiver"],
                "Amount (INR)": b["transaction"]["amount_inr"],
                "Est. (USD)": b["transaction"]["estimated_amount_usd"],
                "Block hash": short(b["hash"], 6),
            } for b in reversed(payments)]
            st.dataframe(
                rows, hide_index=True, use_container_width=True,
                column_config={
                    "Amount (INR)": st.column_config.NumberColumn(format="₹%.2f"),
                    "Est. (USD)": st.column_config.NumberColumn(format="$%.2f"),
                },
            )
        else:
            st.info("No transfers recorded yet. Create one from the New transfer tab.")

        # block inspector
        st.markdown('<div class="sec">Block inspector</div>', unsafe_allow_html=True)
        for block in reversed(chain):
            label = "Genesis" if block["transaction"].get("type") == "GENESIS" else "Cross-border payment"
            with st.expander(f"Block #{block['index']}  ·  {label}",
                             expanded=(block["index"] == len(chain) - 1 and len(chain) > 1)):
                st.caption("TIMESTAMP")
                st.text(fmt_time(block["timestamp"]))
                st.caption("TRANSACTION DATA")
                st.json(block["transaction"])
                st.caption("PREVIOUS HASH")
                st.code(block["previous_hash"], language=None)
                st.caption("BLOCK HASH")
                st.code(block["hash"], language=None)

        # integrity test
        st.markdown('<div class="sec">Integrity test</div>', unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("Alter the most recent recorded amount without recalculating its hash. "
                        "Verification will fail, showing how tampering is detected.")
            x, y = st.columns(2)
            with x:
                if st.button("Simulate tampering", disabled=not payments, use_container_width=True):
                    payments[-1]["transaction"]["amount_inr"] += 1
                    st.rerun()
            with y:
                if st.button("Reset ledger", use_container_width=True):
                    st.session_state.chain = [make_genesis()]
                    st.rerun()

    st.markdown('<div class="foot">Educational demonstration &middot; Python and Streamlit &middot; '
                'No wallet, API key or cryptocurrency required.</div>', unsafe_allow_html=True)
