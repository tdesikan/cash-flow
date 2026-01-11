import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import colorsys
import re

# Page config
st.set_page_config(
    page_title="CashFlow",
    page_icon="💰",
    layout="wide"
)

# Title
st.title("CashFlow - Fund    Visualizer")
st.markdown("Visualize your financial transactions as an interactive Sankey diagram")

# Color palette functions
def generate_category_colors(n, saturation=0.7, lightness=0.6):
    """Generate distinct colors using HSL color space"""
    colors = []
    for i in range(n):
        hue = (i * 360 / n) % 360
        rgb = colorsys.hls_to_rgb(hue / 360, lightness, saturation)
        colors.append(f"rgba({int(rgb[0]*255)}, {int(rgb[1]*255)}, {int(rgb[2]*255)}, 0.6)")
    return colors

def get_income_color(alpha=0.6):
    """Green shades for income"""
    return f"rgba(34, 197, 94, {alpha})"  # Modern green

def get_savings_color(alpha=0.6):
    """Blue for savings"""
    return f"rgba(59, 130, 246, {alpha})"  # Modern blue

def get_income_node_color(alpha=0.8):
    """Darker green for income nodes"""
    return f"rgba(22, 163, 74, {alpha})"

# Sidebar - File Upload
st.sidebar.header("Data Upload")
uploaded_file = st.sidebar.file_uploader("Upload your transactions CSV", type=['csv'])
st.sidebar.caption("Currently works with Copilot Money CSV exports")

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
    st.stop()

# Load data from uploaded file
@st.cache_data
def load_data(file):
    df = pd.read_csv(file, quotechar='"', skipinitialspace=True)
    df['date'] = pd.to_datetime(df['date'])
    df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
    # if multiple tags exist, take first one
    df['tags'] = df['tags'].astype(str).apply(lambda x: x.split(',')[0] if pd.notna(x) and ',' in str(x) else x)
    return df

try:
    df = load_data(uploaded_file)
    st.sidebar.success(f"Loaded {len(df)} transactions")
except Exception as e:
    st.error(f"Error loading CSV file: {e}")
    st.stop()

# Sidebar controls
st.sidebar.header("Filters")

# Date range selector
prev_1y = datetime.now().year - 1
prev_2y = datetime.now().year - 2
date_range_option = st.sidebar.selectbox(
    "Date Range",
    ["All Time", "Last Week", "Last Month", "Last 60 Days", 
    "Last 90 Days", "Last 6 Months", "Last 12 Months", 
    str(prev_1y), str(prev_2y)],
    index=6  # Default to "Last Year"
)

# Calculate date range
end_date = datetime.now()
if date_range_option == "Last Week":
    start_date = end_date - timedelta(days=7)
elif date_range_option == "Last Month":
    start_date = end_date - timedelta(days=30)
elif date_range_option == "Last 60 Days":
    start_date = end_date - timedelta(days=60)
elif date_range_option == "Last 90 Days":
    start_date = end_date - timedelta(days=90)
elif date_range_option == "Last 6 Months":
    start_date = end_date - timedelta(days=180)
elif date_range_option == "Last 12 Months":
    start_date = end_date - timedelta(days=365)
elif date_range_option == str(prev_1y):
    start_date = datetime(prev_1y, 1, 1)
    end_date = datetime(prev_1y, 12, 31)
elif date_range_option == str(prev_2y):
    start_date = datetime(prev_2y, 1, 1)
    end_date = datetime(prev_2y, 12, 31)
else:  # All Time
    start_date = df['date'].min()

# Filter data
filtered_df = df.copy()

# Apply date filter
if date_range_option != "All Time":
    filtered_df = filtered_df[(filtered_df['date'] >= start_date) & (filtered_df['date'] <= end_date)]

# Separate income and expenses
# Income: only transactions of type 'income' or in category 'bonuses'
income_df = filtered_df[
    (filtered_df['type'] == 'income') | 
    (filtered_df['category'].isin(['bonuses']))
]

# Expenses: all non-income transactions with valid categories (positive = expense, negative = refund)
expenses_df = filtered_df[
    (filtered_df['type'] != 'income') & 
    (filtered_df['category'].notna()) & 
    (filtered_df['category'] != '') & 
    (filtered_df['excluded'] != True)
]

# Calculate totals
total_income = income_df['amount'].abs().sum()

# Group expenses by category (positive = expense, negative = refund/credit)
category_totals = expenses_df.groupby('category')['amount'].sum().sort_values(ascending=False)
total_expenses = category_totals.sum()
savings = total_income - total_expenses

# Display metrics
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Income", f"${total_income:,.2f}", delta=None)
with col2:
    st.metric("Expenses", f"${total_expenses:,.2f}", delta=None, delta_color="inverse")
with col3:
    st.metric("Savings", f"${savings:,.2f}", delta=None)
with col4:
    savings_rate = (savings / total_income * 100) if total_income > 0 else 0
    st.metric("Savings Rate", f"{savings_rate:.2f}%", delta=None)

# Create Sankey diagram with flow: Income by Tags → Total Income → Total Expenses → Parent Categories → Categories
# With conditional Deficit (if expenses > income) or Savings (if income > expenses)
labels = []
source = []
target = []
values = []
colors = []

# Group income by tags
income_by_tag = income_df.groupby('tags')['amount'].sum().abs().sort_values(ascending=False)
print(income_by_tag)

# Create income tag nodes (source nodes)
income_tag_indices = {}
for idx, (tag, amount) in enumerate(income_by_tag.items()):
    tag_label = f"Income: {tag}" if pd.notna(tag) and str(tag) != 'nan' else "Income: Untagged"
    labels.append(tag_label)
    income_tag_indices[tag] = idx

# Add Total Income node
total_income_idx = len(labels)
labels.append("Total Income")

# Add Total Expenses node
total_expenses_idx = len(labels)
labels.append("Total Expenses")

# Add Deficit node if expenses exceed income
deficit_idx = None
if savings < 0:
    deficit_idx = len(labels)
    labels.append("Deficit")

# Add Savings node if income exceeds expenses
savings_idx = None
if savings > 0:
    savings_idx = len(labels)
    labels.append("Savings")

# Group expenses by parent category and category
# Sort by absolute values to match what we display in the diagram
parent_category_totals = expenses_df.groupby('parent category')['amount'].sum()
# Sort by absolute value in descending order, preserving index
sorted_indices = parent_category_totals.abs().sort_values(ascending=False).index
parent_category_totals = parent_category_totals.reindex(sorted_indices)
parent_category_category = expenses_df.groupby(['parent category', 'category'])['amount'].sum().reset_index()
print(parent_category_totals)

# Add parent category nodes (intermediate nodes)
parent_category_start_idx = len(labels)
parent_category_indices = {}
for idx, (parent_cat, amount) in enumerate(parent_category_totals.items()):
    parent_label = f"{parent_cat}" if pd.notna(parent_cat) and str(parent_cat) != 'nan' else "Uncategorized"
    labels.append(parent_label)
    parent_category_indices[parent_cat] = parent_category_start_idx + idx

# Add category nodes (destination nodes)
category_start_idx = len(labels)
category_indices = {}
for idx, (category, amount) in enumerate(category_totals.items()):
    labels.append(f"{category}")
    category_indices[category] = category_start_idx + idx

# Create links: Income Tags → Total Income
for tag, income_amount in income_by_tag.items():
    if pd.notna(tag) and tag in income_tag_indices:
        income_idx = income_tag_indices[tag]
        source.append(income_idx)
        target.append(total_income_idx)
        values.append(income_amount)
        colors.append(get_income_color(0.5))  # Green shades for income flow

# Create links: Total Income → Total Expenses
# If deficit, also create link from Deficit → Total Expenses
if savings < 0:
    # Deficit case: Total Income flows to Total Expenses, Deficit also flows to Total Expenses
    source.append(total_income_idx)
    target.append(total_expenses_idx)
    values.append(total_income)
    colors.append("rgba(251, 146, 60, 0.5)")  # Orange for expenses flow
    
    # Deficit link
    source.append(deficit_idx)
    target.append(total_expenses_idx)
    values.append(abs(savings))
    colors.append("rgba(239, 68, 68, 0.5)")  # Red for deficit flow
else:
    # Savings case: Total Income flows to Total Expenses (only expense amount)
    source.append(total_income_idx)
    target.append(total_expenses_idx)
    values.append(total_expenses)
    colors.append("rgba(251, 146, 60, 0.5)")  # Orange for expenses flow

# Generate distinct colors for parent categories
parent_category_colors = generate_category_colors(len(parent_category_totals), saturation=0.65, lightness=0.55)
parent_category_color_map = {cat: parent_category_colors[i] for i, cat in enumerate(parent_category_totals.index)}

# Create links: Total Expenses → Parent Categories
for parent_cat, parent_amount in parent_category_totals.items():
    if pd.notna(parent_cat) and parent_cat in parent_category_indices:
        parent_idx = parent_category_indices[parent_cat]
        source.append(total_expenses_idx)
        target.append(parent_idx)
        values.append(abs(parent_amount))
        colors.append(parent_category_color_map.get(parent_cat, "rgba(150, 150, 150, 0.4)"))

# Create links: Parent Categories → Categories
# Use parent category color with slight variation for categories
category_color_map = {}

for _, row in parent_category_category.iterrows():
    parent_cat = row['parent category']
    category = row['category']
    amount = row['amount']
    
    if pd.notna(parent_cat) and parent_cat in parent_category_indices and category in category_indices:
        parent_idx = parent_category_indices[parent_cat]
        category_idx = category_indices[category]
        source.append(parent_idx)
        target.append(category_idx)
        values.append(abs(amount))
        
        # Use parent category color with slight brightness variation
        if category not in category_color_map:
            parent_color = parent_category_color_map.get(parent_cat, "rgba(150, 150, 150, 0.4)")
            # Extract RGB values and adjust brightness
            rgb_match = re.search(r'rgba\((\d+),\s*(\d+),\s*(\d+),', parent_color)
            if rgb_match:
                r, g, b = int(rgb_match.group(1)), int(rgb_match.group(2)), int(rgb_match.group(3))
                # Slightly brighter for categories
                r = min(255, int(r * 1.15))
                g = min(255, int(g * 1.15))
                b = min(255, int(b * 1.15))
                category_color_map[category] = f"rgba({r}, {g}, {b}, 0.5)"
            else:
                category_color_map[category] = parent_color
        colors.append(category_color_map.get(category, "rgba(150, 150, 150, 0.4)"))

# Create link: Total Expenses → Savings (if positive)
if savings > 0:
    source.append(total_expenses_idx)
    target.append(savings_idx)
    values.append(savings)
    colors.append(get_savings_color(0.5))  # Blue for savings

# Create node colors
node_colors = []
# Colors for income tags (green shades with variation)
income_greens = [
    "rgba(34, 197, 94, 0.85)",   # Bright green
    "rgba(22, 163, 74, 0.85)",   # Medium green
    "rgba(21, 128, 61, 0.85)",   # Darker green
    "rgba(20, 83, 45, 0.85)",    # Dark green
]
for idx in range(len(income_by_tag)):
    node_colors.append(income_greens[idx % len(income_greens)])

# Color for Total Income (green)
node_colors.append(get_income_node_color(0.9))

# Color for Total Expenses (orange/amber)
node_colors.append("rgba(251, 146, 60, 0.85)")  # Orange for expenses

# Color for Deficit (if exists, red)
if savings < 0:
    node_colors.append("rgba(239, 68, 68, 0.85)")  # Red for deficit

# Color for Savings (if exists, blue)
if savings > 0:
    node_colors.append(get_savings_color(0.85))  # Blue for Savings

# Colors for parent categories (use the same colors as flows but with higher opacity)
for parent_cat in parent_category_totals.index:
    parent_color = parent_category_color_map.get(parent_cat, "rgba(150, 150, 150, 0.8)")
    # Increase opacity for nodes
    node_colors.append(parent_color.replace("0.6", "0.85"))

# Colors for categories (use the same colors as flows but with higher opacity)
for category in category_totals.index:
    category_color = category_color_map.get(category, "rgba(150, 150, 150, 0.8)")
    # Increase opacity for nodes
    node_colors.append(category_color.replace("0.5", "0.85").replace("0.4", "0.85"))

# Helper function to format currency
def format_currency(amount):
    """Format currency with K/M suffixes for readability"""
    if abs(amount) >= 1000000:
        return f"${abs(amount)/1000000:.1f}M"
    elif abs(amount) >= 1000:
        return f"${abs(amount)/1000:.1f}K"
    else:
        return f"${abs(amount):,.0f}"

# Helper function to truncate long labels
def truncate_label(label, max_length=25):
    """Truncate label if too long"""
    if len(label) > max_length:
        return label[:max_length-3] + "..."
    return label

# Create custom labels with better formatting (shorter, cleaner)
node_labels = []
for i, label in enumerate(labels):
    if label.startswith("Income: "):
        tag_name = label.replace("Income: ", "")
        if tag_name == "Untagged":
            untagged_income = income_df[income_df['tags'].isna() | (income_df['tags'].astype(str) == 'nan')]['amount'].abs().sum()
            node_labels.append(f"{truncate_label(tag_name, 20)}\n{format_currency(untagged_income)}")
        else:
            tag_amount = income_by_tag.get(tag_name, 0)
            node_labels.append(f"{truncate_label(tag_name, 20)}\n{format_currency(tag_amount)}")
    elif label == "Total Income":
        node_labels.append(f"Total Income\n{format_currency(total_income)}")
    elif label == "Total Expenses":
        node_labels.append(f"Total Expenses\n{format_currency(total_expenses)}")
    elif label == "Deficit":
        node_labels.append(f"Deficit\n{format_currency(abs(savings))}")
    elif label == "Savings":
        savings_pct = savings/total_income*100 if total_income > 0 else 0
        node_labels.append(f"Savings\n{format_currency(savings)}\n{savings_pct:.1f}%")
    elif label in parent_category_indices:
        # This is a parent category
        parent_amount = parent_category_totals.get(label, 0)
        node_labels.append(f"{truncate_label(label, 22)}\n{format_currency(abs(parent_amount))}")
    else:
        # This is a category
        cat_amount = category_totals.get(label, 0)
        node_labels.append(f"{truncate_label(label, 20)}\n{format_currency(abs(cat_amount))}")

fig = go.Figure(data=[go.Sankey(
    node=dict(
        pad=20,
        thickness=25,
        line=dict(color="white", width=2),
        label=node_labels,
        color=node_colors,
        hovertemplate='%{label}<extra></extra>'
    ),
    link=dict(
        source=source,
        target=target,
        value=values,
        color=colors,
        hovertemplate='%{source.label} → %{target.label}<br>Amount: $%{value:,.2f}<extra></extra>'
    ),
    arrangement='snap',
    orientation='h'
)])

fig.update_layout(
    title=dict(
        text="Income Flow: Tags → Total Income → Total Expenses → Parent Categories → Categories",
        font=dict(size=16, color='#1f2937')
    ),
    font=dict(size=13, color='#1f2937', family='Arial, sans-serif'),
    height=700,
    paper_bgcolor='white',
    plot_bgcolor='white'
)

# Add custom CSS to remove text-shadow from Sankey node labels
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

st.plotly_chart(fig, width='stretch')

# Category drill-down section
st.markdown("---")
st.subheader("Category Breakdown")

# Category selector
all_categories = sorted(category_totals.index.tolist())
selected_category = st.selectbox("Select a category to see detailed breakdown:", ["None"] + all_categories, index=0)

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
    
    # Pie chart by merchant/name (exclude negative refunds)
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

# Additional stats
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Transactions", f"{len(filtered_df):,}")
with col2:
    categories = filtered_df['category'].dropna().nunique()
    st.metric("Categories", categories)
with col3:
    accounts = filtered_df['account'].dropna().nunique()
    st.metric("Accounts", accounts)

# Top categories legend
st.subheader("Top Expense Categories")
legend_df = pd.DataFrame({
    'Category': category_totals.head(10).index,
    'Amount': category_totals.head(10).values,
    'Percentage': (category_totals.head(10).values / total_income * 100)
})
legend_df['Amount'] = legend_df['Amount'].apply(lambda x: f"${x:,.2f}")
legend_df['Percentage'] = legend_df['Percentage'].apply(lambda x: f"{x:.2f}%")
st.dataframe(legend_df, hide_index=True, width='stretch')
