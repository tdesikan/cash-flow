"""Data loading, filtering, and processing logic."""
import pandas as pd
from datetime import datetime, timedelta
import streamlit as st


@st.cache_data
def load_data(file):
    """Load and preprocess transaction data from CSV file."""
    df = pd.read_csv(file, quotechar='"', skipinitialspace=True)
    df['date'] = pd.to_datetime(df['date'])
    df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
    # If multiple tags exist, take first one
    df['tags'] = df['tags'].astype(str).apply(
        lambda x: x.split(',')[0] if pd.notna(x) and ',' in str(x) else x
    )
    return df


def calculate_date_range(date_range_option, df):
    """Calculate start and end dates based on date range option."""
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
    elif date_range_option == str(datetime.now().year - 1):
        start_date = datetime(datetime.now().year - 1, 1, 1)
        end_date = datetime(datetime.now().year - 1, 12, 31)
    elif date_range_option == str(datetime.now().year - 2):
        start_date = datetime(datetime.now().year - 2, 1, 1)
        end_date = datetime(datetime.now().year - 2, 12, 31)
    else:  # All Time
        start_date = df['date'].min()
    
    return start_date, end_date


def filter_data(df, date_range_option):
    """Filter data based on date range."""
    filtered_df = df.copy()
    
    if date_range_option != "All Time":
        start_date, end_date = calculate_date_range(date_range_option, df)
        filtered_df = filtered_df[
            (filtered_df['date'] >= start_date) & 
            (filtered_df['date'] <= end_date)
        ]
    
    return filtered_df


def separate_income_and_expenses(filtered_df):
    """Separate transactions into income and expenses dataframes."""
    # Income: only transactions of type 'income' or in category 'bonuses'
    income_df = filtered_df[
        (filtered_df['type'] == 'income') | 
        (filtered_df['category'].isin(['bonuses', 'Bonuses']))
    ]
    
    # Expenses: all non-income transactions with valid categories
    expenses_df = filtered_df[
        (filtered_df['type'] != 'income') & 
        (filtered_df['category'].notna()) & 
        (filtered_df['category'] != '') & 
        (filtered_df['excluded'] != True)
    ]
    
    return income_df, expenses_df


def calculate_financial_metrics(income_df, expenses_df):
    """Calculate total income, expenses, savings, and related metrics."""
    total_income = income_df['amount'].abs().sum()
    
    # Group expenses by category
    category_totals = expenses_df.groupby('category')['amount'].sum().sort_values(ascending=False)
    total_expenses = category_totals.sum()
    savings = total_income - total_expenses
    
    return {
        'total_income': total_income,
        'total_expenses': total_expenses,
        'savings': savings,
        'category_totals': category_totals,
        'savings_rate': (savings / total_income * 100) if total_income > 0 else 0
    }


def prepare_sankey_data(income_df, expenses_df, category_totals):
    """Prepare data structures needed for Sankey diagram."""
    # Group income by tags
    income_by_tag = income_df.groupby('tags')['amount'].sum().abs().sort_values(ascending=False)
    
    # Group expenses by parent category and category
    parent_category_totals = expenses_df.groupby('parent category')['amount'].sum()
    # Sort by absolute value in descending order, preserving index
    sorted_indices = parent_category_totals.abs().sort_values(ascending=False).index
    parent_category_totals = parent_category_totals.reindex(sorted_indices)
    
    parent_category_category = expenses_df.groupby(['parent category', 'category'])['amount'].sum().reset_index()
    
    return {
        'income_by_tag': income_by_tag,
        'parent_category_totals': parent_category_totals,
        'parent_category_category': parent_category_category,
        'category_totals': category_totals
    }
