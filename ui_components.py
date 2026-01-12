"""Streamlit UI components."""
import streamlit as st
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
        - `parent category`: Expense category grouping
        - `category`: Expense category
        - `excluded`: Category is to be excluded from the analysis
        - `tags`: Labels associated with a transaction
        - `type`: Transaction type (`income`, `regular`, etc.)
        - `account`: Account name
        - `excluded`: Whether to exclude (true/false)
        
        #### Sample format:
        ```csv
        date,name,amount,status,category,tags,type,account,excluded
        2026-01-01,Salary,-5000.00,cleared,Salary,0-v-snow,income,Checking,false
        2026-01-02,Grocery Store,85.50,cleared,Food & Dining,0-v-snow,regular,Credit Card,false
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
        ["All Time", "Last Week", "Last Month", "Last 60 Days", 
         "Last 90 Days", "Last 6 Months", "Last 12 Months", 
         str(prev_1y), str(prev_2y)],
        index=6  # Default to "Last Year"
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
