# gui/blockchain_audit_view.py

import streamlit as st

def render_blockchain(chain):

    st.header("🔗 Federated Audit Ledger")

    for block in chain[-10:]:
        st.write(f"Timestamp: {block['record']['timestamp']}")
        st.code(block["hash"])