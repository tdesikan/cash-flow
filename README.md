# CashFlow - Transaction Flow Visualizer

A Streamlit web application that visualizes your financial transactions as an interactive Sankey diagram, showing how income flows into savings and various expense categories.

![Transaction Flow Visualization](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)

## Features

- **Interactive Sankey Diagram**: Visualize income flow to savings and expense categories
- **Multiple Date Ranges**: View transactions for different time periods (Last Week, Month, 60/90 days, 6 months, Year, All Time)
- **Key Metrics Dashboard**: Track Income, Expenses, Savings, and Savings Rate
- **Category Drill-Down**: Click on any category to see:
  - Top 10 merchants/payees in that category (pie chart)
  - Detailed transaction table
  - Category-specific metrics
- **Percentage-Based Labels**: Node labels show percentages of income for easy comparison
- **Automatic Refund Handling**: Negative amounts are properly handled as refunds that reduce expenses
- **CSV File Upload**: Direct upload of transaction CSV files - no manual file placement needed

## Requirements

**CSV Format:** This is a generic transaction flow visualizer. Currently tested and working with CSV exports from [Copilot Money](https://copilot.money).

Your CSV file should include these columns:
- `date` - Transaction date
- `name` - Merchant/payee name  
- `amount` - Transaction amount (negative for income, positive for expenses)
- `type` - Transaction type (e.g., `income`, `regular`)
- `category` - Expense category
- `account` - Account name
- `excluded` - Whether to exclude (true/false)

## Demo

The app displays:
- **Income** flows into **Savings** and various **Expense Categories**
- Each category shows its percentage of total income
- Interactive category selection for detailed merchant breakdowns
- Real-time metrics update based on selected date range

## Installation

1. Clone this repository:
```bash
git clone https://github.com/KushalBKusram/CashFlow.git
cd CashFlow
```

2. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Run the Streamlit app:
```bash
streamlit run app.py
```

2. Open your browser to `http://localhost:8501`

3. Export your transactions from **Copilot Money** app and upload the CSV file using the file uploader in the sidebar

That's it! The app will automatically process your transactions and visualize them.

## Customization

### Date Range Presets
Modify the date range options in [app.py](app.py):
```python
date_range_option = st.sidebar.selectbox(
    "Date Range",
    ["All Time", "Last Week", "Last Month", ...],
    index=2  # Default selection
)
```

### Category Colors
The Sankey diagram automatically generates colors for categories, but you can customize them in the code by modifying the color generation logic.

### Filters
The app currently filters:
- By date range (user selectable)
- Excludes transactions with empty categories (for expenses)
- Handles income vs expense separation based on transaction type

## Tech Stack

- **[Streamlit](https://streamlit.io/)**: Web application framework (v1.50.0)
- **[Pandas](https://pandas.pydata.org/)**: Data manipulation (v2.3.3)
- **[Plotly](https://plotly.com/python/)**: Interactive visualizations (v6.5.0)
- **Python**: 3.9+

## Project Structure

```
CashFlow/
├── app.py                       # Main Streamlit application
├── requirements.txt             # Python dependencies
├── .gitignore                   # Git ignore rules
└── README.md                    # This file
```

## Features Explained

### Income Calculation
- Only transactions with `type == 'income'` are counted as income
- Uses absolute value of amount (since income is stored as negative)

### Expense Calculation
- All non-income transactions with valid categories
- Sum includes negative amounts (refunds) which reduce category totals
- Excluded transactions are filtered out

### Savings Calculation
```
Savings = Total Income - Total Expenses
Savings Rate = (Savings / Income) × 100%
```

### Category Drill-Down
When you select a category:
1. **Pie Chart**: Shows top 10 merchants/payees by spending
2. **Transaction Table**: Lists up to 20 recent transactions in that category
3. **Metrics**: Total spent, transaction count, average transaction size

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - feel free to use this project for personal or commercial purposes.

## Acknowledgments

- Built with [Streamlit](https://streamlit.io/)
- Visualization powered by [Plotly](https://plotly.com/)
- Inspired by financial tracking needs and data visualization best practices

## Support

If you find this useful, please star ⭐ the repository!

For issues or questions, please open an issue on GitHub.

---

**Note**: Currently supports CSV exports from **Copilot Money** app. Export your transactions from Copilot Money and upload them through the web interface. Future versions may support additional financial apps.
