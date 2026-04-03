"""Streamlit UI components."""
import json

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime


def render_file_upload():
    """Render file upload section and return uploaded file."""
    st.sidebar.header("Data Upload")
    uploaded_file = st.sidebar.file_uploader("Upload Copilot Money CSV export", type=['csv'])
    
    if uploaded_file is None:
        st.info("Please upload your transaction CSV file (currently supports Copilot Money export format)")
        st.markdown("""
        ### Expected CSV Format
        
        Your CSV file should include these columns:
        - `date`: Transaction date (YYYY-MM-DD)
        - `name`: Merchant/payee name
        - `amount`: Transaction amount (negative for income/refunds, positive for expenses)
        - `category`: Expense category - only 1 category per transaction
        - `parent category`: Expense category grouping - every category should have a parent category
        - `excluded`: Category is to be excluded from the analysis
        - `tags`: Labels associated with a transaction - can have no tags or multiple tags per transaction
        - `type`: Transaction type (`income`, `regular`, etc.)
        - `account`: Account name
        - `excluded`: Whether to exclude (true/false)
        
        #### Sample format:
        ```csv
        date,name,amount,status,category,tags,type,account,excluded
        2026-01-01,Salary,-5000.00,cleared,Salary,0-v-snow,income,Checking,false
        2026-01-02,Grocery Store,85.50,cleared,Food & Dining,"0-v-Snow, TODO",regular,Credit Card,false
        ```
        """)
        return None
    
    return uploaded_file


def render_filters():
    """Render date range selector and return selected option."""
    st.sidebar.header("Filters")
    
    prev_1y = datetime.now().year - 1
    prev_2y = datetime.now().year - 2
    date_range_option = st.sidebar.selectbox(
        "Date Range",
        ["Year to date", "Month to date", 
        "Last 12 Months", "Last 3 Months", "Last 4 Weeks",
         str(prev_1y), str(prev_2y), "All Time"],
        index=5  # Default to "Last Year"
    )

    lumpy_option = st.sidebar.checkbox("Include Bonuses, Taxes, and other Lumpy categories", value=False)
    
    return date_range_option, lumpy_option


def render_metrics(metrics):
    """Render financial metrics."""
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Income", f"${metrics['total_income']:,.2f}", delta=None)
    with col2:
        st.metric("Expenses", f"${metrics['total_expenses']:,.2f}", delta=None, delta_color="inverse")
    with col3:
        st.metric("Savings", f"${metrics['savings']:,.2f}", delta=None)
    with col4:
        st.metric("Savings Rate", f"{metrics['savings_rate']:.2f}%", delta=None)


def render_sankey_css():
    """Render custom CSS for Sankey diagram."""
    st.markdown("""
    <style>
        /* Remove text-shadow from all Plotly Sankey node labels */
        .js-plotly-plot svg text,
        .plotly svg text,
        svg text {
            text-shadow: none !important;
            filter: none !important;
        }
    </style>
    """, unsafe_allow_html=True)


def render_sankey_chart(fig, parent_node_indices, total_expenses_idx):
    """Render Sankey via HTML for label tweaks not exposed in Plotly.py (leaf-calibrated x; parents keep Plotly y)."""
    idx_json = json.dumps(list(parent_node_indices))
    te = int(total_expenses_idx)
    # Raw JS only: Plotly injects post_script inside its own <script> block; do not wrap in <script>.
    post_script = f"""
    (function () {{
      var PARENT_IDX = {idx_json};
      var TOTAL_EXPENSES_IDX = {te};
      function groupX(g) {{
        var tr = g.getAttribute('transform') || '';
        var m = tr.match(/translate\\(\\s*([^,\\s]+)\\s*,\\s*([^)]+)\\)/);
        return m ? parseFloat(m[1]) : NaN;
      }}
      function inferLeafPadAndAnchor(nodes) {{
        var maxX = -Infinity;
        for (var a = 0; a < nodes.length; a++) {{
          var gx = groupX(nodes[a]);
          if (!isNaN(gx) && gx > maxX) maxX = gx;
        }}
        if (!isFinite(maxX)) return null;
        for (var b = 0; b < nodes.length; b++) {{
          if (Math.abs(groupX(nodes[b]) - maxX) > 0.5) continue;
          var rect = nodes[b].querySelector('.node-rect');
          var lab = nodes[b].querySelector('text.node-label');
          if (!rect || !lab) continue;
          var lw = parseFloat(rect.getAttribute('width')) || 0;
          var ltr = lab.getAttribute('transform') || '';
          var lm = ltr.match(/translate\\(\\s*([^,\\s]+)\\s*,\\s*([^)]+)\\)/);
          if (!lm) continue;
          var lx = parseFloat(lm[1]);
          var pad = -lx - lw / 2;
          var anchor = lab.getAttribute('text-anchor');
          return {{ pad: pad, anchor: anchor }};
        }}
        return null;
      }}
      function setSankeyLabelAnchors(gd) {{
        if (!gd || !gd.querySelectorAll) return;
        var nodes = gd.querySelectorAll('.sankey-node');
        var ref = inferLeafPadAndAnchor(nodes);
        var pad = ref ? ref.pad : 4;
        var leafAnchor = ref && ref.anchor ? ref.anchor : 'end';
        for (var k = 0; k < PARENT_IDX.length; k++) {{
          var pi = PARENT_IDX[k];
          if (pi < 0 || pi >= nodes.length) continue;
          var pNode = nodes[pi];
          var pRect = pNode.querySelector('.node-rect');
          var pw = pRect ? parseFloat(pRect.getAttribute('width')) : 25;
          var xLeftP = -(pw / 2 + pad);
          var pTexts = pNode.querySelectorAll('text.node-label');
          for (var j = 0; j < pTexts.length; j++) {{
            var ptext = pTexts[j];
            var ptr = ptext.getAttribute('transform') || '';
            var pm = ptr.match(/translate\\(\\s*([^,\\s]+)\\s*,\\s*([^)]+)\\)/);
            var yKeep = pm ? pm[2].trim() : '0';
            ptext.setAttribute('text-anchor', leafAnchor);
            ptext.setAttribute('transform', 'translate(' + xLeftP + ',' + yKeep + ')');
          }}
        }}
        if (TOTAL_EXPENSES_IDX >= 0 && TOTAL_EXPENSES_IDX < nodes.length) {{
          var teNode = nodes[TOTAL_EXPENSES_IDX];
          var teTexts = teNode.querySelectorAll('text.node-label');
          var teRect = teNode.querySelector('.node-rect');
          var rw = teRect ? parseFloat(teRect.getAttribute('width')) : 25;
          var xLeft = -(rw / 2 + pad);
          for (var t = 0; t < teTexts.length; t++) {{
            var tnode = teTexts[t];
            tnode.setAttribute('text-anchor', leafAnchor);
            var fs = parseFloat(window.getComputedStyle(tnode).fontSize) || 13;
            var yTop = fs * 3;
            tnode.setAttribute('transform', 'translate(' + xLeft + ',' + yTop + ')');
          }}
        }}
      }}
      var gd = document.getElementById('cashflow-sankey');
      if (!gd) return;
      gd.on('plotly_afterplot', function () {{ setSankeyLabelAnchors(gd); }});
      setTimeout(function () {{ setSankeyLabelAnchors(gd); }}, 0);
    }})();
    """
    html = fig.to_html(
        full_html=True,
        include_plotlyjs="cdn",
        div_id="cashflow-sankey",
        config={"responsive": True, "displayModeBar": True},
        post_script=post_script,
    )
    components.html(html, height=760, scrolling=False)


def render_category_breakdown(expenses_df, category_totals, total_income):
    """Render category breakdown section."""
    st.markdown("---")
    st.subheader("Category Breakdown")
    
    # Category selector
    all_categories = sorted(category_totals.index.tolist())
    selected_category = st.selectbox(
        "Select a category to see detailed breakdown:", 
        ["None"] + all_categories, 
        index=0
    )
    
    if selected_category != "None":
        # Filter transactions for selected category
        category_transactions = expenses_df[expenses_df['category'] == selected_category]
        
        st.markdown(f"### {selected_category}")
        
        # Summary metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            category_total = category_transactions['amount'].sum()
            st.metric("Total Spent", f"${category_total:,.2f}")
        with col2:
            st.metric("Transactions", len(category_transactions))
        with col3:
            avg_transaction = category_total / len(category_transactions) if len(category_transactions) > 0 else 0
            st.metric("Avg Transaction", f"${avg_transaction:,.2f}")
        
        # Pie chart by merchant/name
        positive_transactions = category_transactions[category_transactions['amount'] > 0]
        merchant_totals = positive_transactions.groupby('name')['amount'].sum().sort_values(ascending=False).head(10)
        
        if len(merchant_totals) > 0:
            # Create pie chart
            fig_pie = go.Figure(data=[go.Pie(
                labels=merchant_totals.index,
                values=merchant_totals.values,
                hole=0.3,
                textposition='auto',
                textinfo='label+percent'
            )])
            
            fig_pie.update_layout(
                title=f"Top Merchants/Payees in {selected_category}",
                height=500,
                showlegend=True
            )
            
            st.plotly_chart(fig_pie, width='stretch')
            
            # Detailed transaction table
            st.markdown("### Recent Transactions")
            transaction_display = category_transactions[['date', 'name', 'amount', 'account']].copy()
            transaction_display['date'] = pd.to_datetime(transaction_display['date']).dt.strftime('%Y-%m-%d')
            transaction_display['amount'] = transaction_display['amount'].apply(lambda x: f"${x:,.2f}")
            transaction_display = transaction_display.sort_values('date', ascending=False).head(20)
            st.dataframe(transaction_display, hide_index=True, width='stretch')


def render_additional_stats(filtered_df):
    """Render additional statistics."""
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Transactions", f"{len(filtered_df):,}")
    with col2:
        categories = filtered_df['category'].dropna().nunique()
        st.metric("Categories", categories)
    with col3:
        accounts = filtered_df['account'].dropna().nunique()
        st.metric("Accounts", accounts)


def render_top_categories(category_totals, total_income):
    """Render top expense categories table."""
    st.subheader("Top Expense Categories")
    legend_df = pd.DataFrame({
        'Category': category_totals.head(10).index,
        'Amount': category_totals.head(10).values,
        'Percentage': (category_totals.head(10).values / total_income * 100)
    })
    legend_df['Amount'] = legend_df['Amount'].apply(lambda x: f"${x:,.2f}")
    legend_df['Percentage'] = legend_df['Percentage'].apply(lambda x: f"{x:.2f}%")
    st.dataframe(legend_df, hide_index=True, width='stretch')


def render_tags_breakdown(expenses_df):
    """Render tags breakdown section (0–many tags per transaction)."""
    st.markdown("---")
    st.subheader("Tags Breakdown")

    if 'tags' not in expenses_df.columns:
        st.info("No tags data available in this dataset.")
        return

    # Prepare exploded dataframe with one row per (transaction, tag)
    tagged = expenses_df.copy()
    tagged['tags'] = tagged['tags'].fillna('').astype(str)
    tagged = tagged[tagged['tags'].str.strip() != '']

    if tagged.empty:
        st.info("No tags found in the current filtered transactions.")
        return

    tagged = tagged.assign(tag_list=tagged['tags'].str.split(','))
    exploded = tagged.explode('tag_list')
    exploded['tag_list'] = exploded['tag_list'].astype(str).str.strip()
    exploded = exploded[exploded['tag_list'] != '']

    if exploded.empty:
        st.info("No tags found in the current filtered transactions.")
        return

    # Aggregate totals by tag
    tag_totals = (
        exploded.groupby('tag_list')['amount']
        .sum()
        .sort_values(ascending=False)
    )

    all_tags = tag_totals.index.tolist()

    selected_tag = st.selectbox(
        "Select a tag to see detailed breakdown:",
        ["None"] + all_tags,
        index=0,
    )

    if selected_tag == "None":
        return

    tag_transactions = exploded[exploded['tag_list'] == selected_tag]

    st.markdown(f"### {selected_tag}")

    # Summary metrics for this tag
    col1, col2, col3 = st.columns(3)
    with col1:
        total_spent = tag_transactions['amount'].sum()
        st.metric("Total Spent", f"${total_spent:,.2f}")
    with col2:
        txn_count = tag_transactions.drop_duplicates(
            subset=['date', 'name', 'amount', 'account']
        ).shape[0]
        st.metric("Transactions", txn_count)
    with col3:
        avg_transaction = total_spent / txn_count if txn_count > 0 else 0
        st.metric("Avg Transaction", f"${avg_transaction:,.2f}")

    # Pie chart by category within this tag
    positive_transactions = tag_transactions[tag_transactions['amount'] > 0]
    if not positive_transactions.empty and 'category' in positive_transactions.columns:
        category_totals = (
            positive_transactions.groupby('category')['amount']
            .sum()
            .sort_values(ascending=False)
            .head(10)
        )

        if len(category_totals) > 0:
            fig_pie = go.Figure(
                data=[
                    go.Pie(
                        labels=category_totals.index,
                        values=category_totals.values,
                        hole=0.3,
                        textposition="auto",
                        textinfo="label+percent",
                    )
                ]
            )

            fig_pie.update_layout(
                title=f"Top Categories for Tag: {selected_tag}",
                height=500,
                showlegend=True,
            )

            st.plotly_chart(fig_pie, width="stretch")

    # Detailed transaction table (deduplicated per transaction)
    st.markdown("### Recent Transactions")
    transaction_display = (
        tag_transactions.drop_duplicates(
            subset=['date', 'name', 'amount', 'account']
        )[['date', 'name', 'category', 'amount', 'account', 'tags']]
        .copy()
    )
    transaction_display['date'] = pd.to_datetime(
        transaction_display['date']
    ).dt.strftime('%Y-%m-%d')
    transaction_display['amount'] = transaction_display['amount'].apply(
        lambda x: f"${x:,.2f}"
    )
    transaction_display = transaction_display.sort_values(
        'date', ascending=False
    ).head(50)
    st.dataframe(transaction_display, hide_index=True, width='stretch')
