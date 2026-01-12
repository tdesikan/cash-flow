"""Main Streamlit application for CashFlow visualization."""
import streamlit as st

from data_processing import (
    load_data, filter_data, separate_income_and_expenses,
    calculate_financial_metrics, prepare_sankey_data
)
from sankey_builder import SankeyBuilder
from ui_components import (
    render_file_upload, render_filters, render_metrics,
    render_sankey_css, render_category_breakdown, render_additional_stats,
    render_top_categories
)

# Page config
st.set_page_config(
    page_title="CashFlow",
    page_icon="💰",
    layout="wide"
)

# Title
st.title("TD SS CashFlow Visualizer")
st.markdown("Visualize income & spending as an interactive Sankey diagram")

# File upload
uploaded_file = render_file_upload()
if uploaded_file is None:
    st.stop()

# Load data
try:
    df = load_data(uploaded_file)
    st.sidebar.success(f"Loaded {len(df)} transactions")
except Exception as e:
    st.error(f"Error loading CSV file: {e}")
    st.stop()

# Filters - date range selector
date_range_option, lumpy_option = render_filters()

# Filter data
filtered_df = filter_data(df, date_range_option, lumpy_option)

# Separate income and expenses
income_df, expenses_df = separate_income_and_expenses(filtered_df)

# Calculate metrics
metrics = calculate_financial_metrics(income_df, expenses_df)

# Display metrics
render_metrics(metrics)

# Prepare Sankey data
sankey_data = prepare_sankey_data(
    income_df, 
    expenses_df, 
    metrics['category_totals']
)

# Build Sankey diagram
sankey_builder = SankeyBuilder(sankey_data, metrics, income_df)
fig = sankey_builder.build()

# Render Sankey CSS
render_sankey_css()

# Display Sankey diagram
st.plotly_chart(fig, width='stretch')

# Category breakdown
render_category_breakdown(
    expenses_df, 
    metrics['category_totals'], 
    metrics['total_income']
)

# Additional stats
render_additional_stats(filtered_df)

# Top categories
render_top_categories(metrics['category_totals'], metrics['total_income'])
