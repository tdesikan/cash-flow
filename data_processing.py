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
    prev_1y = datetime.now().year - 1
    prev_2y = datetime.now().year - 2
    
    if date_range_option == "Year to date":
        start_date = datetime(end_date.year, 1, 1)
    elif date_range_option == "Month to date":
        start_date = datetime(end_date.year, end_date.month, 1)
    elif date_range_option == "Last 12 Months":
        start_date = end_date.replace(day=1)
        months_back = 12 if end_date.day == 1 else 11
        for _ in range(months_back):
            start_date = (start_date - timedelta(days=1)).replace(day=1)
    elif date_range_option == "Last 3 Months":
        start_date = end_date.replace(day=1)
        for _ in range(3):
            start_date = (start_date - timedelta(days=1)).replace(day=1)
    elif date_range_option == "Last 4 Weeks":
        start_date = end_date - timedelta(weeks=4)
    elif date_range_option == str(prev_1y):
        start_date = datetime(prev_1y, 1, 1)
        end_date = datetime(prev_1y, 12, 31)
    elif date_range_option == str(prev_2y):
        start_date = datetime(prev_2y, 1, 1)
        end_date = datetime(prev_2y, 12, 31)
    else:  # All Time
        start_date = df['date'].min()
    
    print(start_date, end_date)
    return start_date, end_date


def filter_data(df, date_range_option, lumpy_option):
    """Filter data based on date range."""
    filtered_df = df.copy()
    
    # Always remove some categories from analysis
    filtered_df = filtered_df[~filtered_df['category'].isin([
        'Investments & Assets',
        'Credit Card Reconciliation', 
        'TD Reimbursed', 
        'SS Reimbursed'
    ])]

    if date_range_option != "All Time":
        start_date, end_date = calculate_date_range(date_range_option, df)
        filtered_df = filtered_df[
            (filtered_df['date'] >= start_date) & 
            (filtered_df['date'] <= end_date)
        ]
    
    # parent_category Lumpy removed unless we ask for it
    if not lumpy_option:
        filtered_df = filtered_df[filtered_df['parent category'] != 'Lumpy']
    
    return filtered_df


def separate_income_and_expenses(filtered_df):
    """Separate transactions into income and expenses dataframes."""
    # Income: only transactions of type 'income' 
    # Note: category 'Bonuses' under parent 'Lumpy' is actually income
    income_df = filtered_df[
        (filtered_df['type'] == 'income') | 
        (filtered_df['category'] == 'Bonuses')
    ]

    # Expenses: all non-income transactions with valid categories
    expenses_df = filtered_df[
        (filtered_df['type'] != 'income') & 
        (filtered_df['category'] != 'Bonuses') &
        (filtered_df['category'].notna()) & 
        (filtered_df['category'] != '')
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
