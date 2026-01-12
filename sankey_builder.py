"""Sankey diagram construction logic."""
import pandas as pd
import plotly.graph_objects as go
import re
from colors import (
    generate_category_colors, get_income_color, get_savings_color,
    get_income_node_color, get_income_tag_colors
)
from utils import format_currency, truncate_label


class SankeyBuilder:
    """Builds Sankey diagram from financial data."""
    
    def __init__(self, sankey_data, metrics, income_df):
        """Initialize with data and metrics."""
        self.sankey_data = sankey_data
        self.metrics = metrics
        self.income_df = income_df
        
        self.labels = []
        self.source = []
        self.target = []
        self.values = []
        self.colors = []
        
        # Index mappings
        self.income_tag_indices = {}
        self.parent_category_indices = {}
        self.category_indices = {}
        self.parent_category_label_map = {}  # Map from label to parent_cat
        
        # Color maps
        self.parent_category_color_map = {}
        self.category_color_map = {}
        
    def build(self):
        """Build the complete Sankey diagram."""
        self._create_nodes()
        self._create_links()
        self._create_node_colors()
        self._create_node_labels()
        return self._create_figure()
    
    def _create_nodes(self):
        """Create all nodes in the Sankey diagram."""
        # Income tag nodes
        for idx, (tag, amount) in enumerate(self.sankey_data['income_by_tag'].items()):
            tag_label = f"Income: {tag}" if pd.notna(tag) and str(tag) != 'nan' else "Income: Untagged"
            self.labels.append(tag_label)
            self.income_tag_indices[tag] = idx
        
        # Total Income node
        self.total_income_idx = len(self.labels)
        self.labels.append("Total Income")
        
        # Total Expenses node
        self.total_expenses_idx = len(self.labels)
        self.labels.append("Total Expenses")
        
        # Deficit node (if expenses exceed income)
        self.deficit_idx = None
        if self.metrics['savings'] < 0:
            self.deficit_idx = len(self.labels)
            self.labels.append("Deficit")
        
        # Savings node (if income exceeds expenses)
        self.savings_idx = None
        if self.metrics['savings'] > 0:
            self.savings_idx = len(self.labels)
            self.labels.append("Savings")
        
        # Parent category nodes
        parent_category_start_idx = len(self.labels)
        self.parent_category_label_map = {}  # Map from label to parent_cat
        for idx, (parent_cat, amount) in enumerate(self.sankey_data['parent_category_totals'].items()):
            parent_label = f"{parent_cat}" if pd.notna(parent_cat) and str(parent_cat) != 'nan' else "Uncategorized"
            self.labels.append(parent_label)
            self.parent_category_indices[parent_cat] = parent_category_start_idx + idx
            self.parent_category_label_map[parent_label] = parent_cat
        
        # Category nodes
        category_start_idx = len(self.labels)
        for idx, (category, amount) in enumerate(self.sankey_data['category_totals'].items()):
            self.labels.append(f"{category}")
            self.category_indices[category] = category_start_idx + idx
    
    def _create_links(self):
        """Create all links in the Sankey diagram."""
        # Income Tags → Total Income
        for tag, income_amount in self.sankey_data['income_by_tag'].items():
            if pd.notna(tag) and tag in self.income_tag_indices:
                income_idx = self.income_tag_indices[tag]
                self.source.append(income_idx)
                self.target.append(self.total_income_idx)
                self.values.append(income_amount)
                self.colors.append(get_income_color(0.5))
        
        # Total Income → Total Expenses (with conditional Deficit)
        if self.metrics['savings'] < 0:
            # Deficit case: Total Income flows to Total Expenses, Deficit also flows to Total Expenses
            self.source.append(self.total_income_idx)
            self.target.append(self.total_expenses_idx)
            self.values.append(self.metrics['total_income'])
            self.colors.append("rgba(251, 146, 60, 0.5)")  # Orange
            
            # Deficit link
            self.source.append(self.deficit_idx)
            self.target.append(self.total_expenses_idx)
            self.values.append(abs(self.metrics['savings']))
            self.colors.append("rgba(239, 68, 68, 0.5)")  # Red
        else:
            # Savings case: Total Income flows to Total Expenses
            self.source.append(self.total_income_idx)
            self.target.append(self.total_expenses_idx)
            self.values.append(self.metrics['total_expenses'])
            self.colors.append("rgba(251, 146, 60, 0.5)")  # Orange
        
        # Generate colors for parent categories
        parent_category_colors = generate_category_colors(
            len(self.sankey_data['parent_category_totals']), 
            saturation=0.65, 
            lightness=0.55
        )
        self.parent_category_color_map = {
            cat: parent_category_colors[i] 
            for i, cat in enumerate(self.sankey_data['parent_category_totals'].index)
        }
        
        # Total Expenses → Parent Categories
        for parent_cat, parent_amount in self.sankey_data['parent_category_totals'].items():
            if pd.notna(parent_cat) and parent_cat in self.parent_category_indices:
                parent_idx = self.parent_category_indices[parent_cat]
                self.source.append(self.total_expenses_idx)
                self.target.append(parent_idx)
                self.values.append(abs(parent_amount))
                self.colors.append(self.parent_category_color_map.get(parent_cat, "rgba(150, 150, 150, 0.4)"))
        
        # Parent Categories → Categories
        for _, row in self.sankey_data['parent_category_category'].iterrows():
            parent_cat = row['parent category']
            category = row['category']
            amount = row['amount']
            
            if (pd.notna(parent_cat) and parent_cat in self.parent_category_indices and 
                category in self.category_indices):
                parent_idx = self.parent_category_indices[parent_cat]
                category_idx = self.category_indices[category]
                self.source.append(parent_idx)
                self.target.append(category_idx)
                self.values.append(abs(amount))
                
                # Use parent category color with slight brightness variation
                if category not in self.category_color_map:
                    parent_color = self.parent_category_color_map.get(parent_cat, "rgba(150, 150, 150, 0.4)")
                    rgb_match = re.search(r'rgba\((\d+),\s*(\d+),\s*(\d+),', parent_color)
                    if rgb_match:
                        r, g, b = int(rgb_match.group(1)), int(rgb_match.group(2)), int(rgb_match.group(3))
                        r = min(255, int(r * 1.15))
                        g = min(255, int(g * 1.15))
                        b = min(255, int(b * 1.15))
                        self.category_color_map[category] = f"rgba({r}, {g}, {b}, 0.5)"
                    else:
                        self.category_color_map[category] = parent_color
                self.colors.append(self.category_color_map.get(category, "rgba(150, 150, 150, 0.4)"))
        
        # Total Expenses → Savings (if positive)
        if self.metrics['savings'] > 0:
            self.source.append(self.total_expenses_idx)
            self.target.append(self.savings_idx)
            self.values.append(self.metrics['savings'])
            self.colors.append(get_savings_color(0.5))
    
    def _create_node_colors(self):
        """Create colors for all nodes."""
        self.node_colors = []
        
        # Income tag colors
        income_greens = get_income_tag_colors(len(self.sankey_data['income_by_tag']))
        for idx in range(len(self.sankey_data['income_by_tag'])):
            self.node_colors.append(income_greens[idx % len(income_greens)])
        
        # Total Income
        self.node_colors.append(get_income_node_color(0.9))
        
        # Total Expenses
        self.node_colors.append("rgba(251, 146, 60, 0.85)")  # Orange
        
        # Deficit (if exists)
        if self.metrics['savings'] < 0:
            self.node_colors.append("rgba(239, 68, 68, 0.85)")  # Red
        
        # Savings (if exists)
        if self.metrics['savings'] > 0:
            self.node_colors.append(get_savings_color(0.85))
        
        # Parent categories
        for parent_cat in self.sankey_data['parent_category_totals'].index:
            parent_color = self.parent_category_color_map.get(parent_cat, "rgba(150, 150, 150, 0.8)")
            self.node_colors.append(parent_color.replace("0.6", "0.85"))
        
        # Categories
        for category in self.sankey_data['category_totals'].index:
            category_color = self.category_color_map.get(category, "rgba(150, 150, 150, 0.8)")
            self.node_colors.append(category_color.replace("0.5", "0.85").replace("0.4", "0.85"))
    
    def _create_node_labels(self):
        """Create formatted labels for all nodes."""
        self.node_labels = []
        
        for i, label in enumerate(self.labels):
            if label.startswith("Income: "):
                tag_name = label.replace("Income: ", "")
                if tag_name == "Untagged":
                    untagged_income = self.income_df[
                        self.income_df['tags'].isna() | 
                        (self.income_df['tags'].astype(str) == 'nan')
                    ]['amount'].abs().sum()
                    self.node_labels.append(
                        f"{truncate_label(tag_name, 20)}\n{format_currency(untagged_income)}"
                    )
                else:
                    tag_amount = self.sankey_data['income_by_tag'].get(tag_name, 0)
                    self.node_labels.append(
                        f"{truncate_label(tag_name, 20)}\n{format_currency(tag_amount)}"
                    )
            elif label == "Total Income":
                self.node_labels.append(f"Total Income\n{format_currency(self.metrics['total_income'])}")
            elif label == "Total Expenses":
                self.node_labels.append(f"Total Expenses\n{format_currency(self.metrics['total_expenses'])}")
            elif label == "Deficit":
                self.node_labels.append(f"Deficit\n{format_currency(abs(self.metrics['savings']))}")
            elif label == "Savings":
                savings_pct = self.metrics['savings_rate']
                self.node_labels.append(
                    f"Savings\n{format_currency(self.metrics['savings'])}\n{savings_pct:.1f}%"
                )
            elif label in self.parent_category_label_map:
                # This is a parent category
                parent_cat = self.parent_category_label_map[label]
                parent_amount = self.sankey_data['parent_category_totals'].get(parent_cat, 0)
                self.node_labels.append(
                    f"{truncate_label(label, 22)}\n{format_currency(abs(parent_amount))}"
                )
            else:
                # This is a category
                cat_amount = self.sankey_data['category_totals'].get(label, 0)
                self.node_labels.append(
                    f"{truncate_label(label, 20)}\n{format_currency(abs(cat_amount))}"
                )
    
    def _create_figure(self):
        """Create the Plotly figure."""
        fig = go.Figure(data=[go.Sankey(
            node=dict(
                pad=20,
                thickness=25,
                line=dict(color="white", width=2),
                label=self.node_labels,
                color=self.node_colors,
                hovertemplate='%{label}<extra></extra>'
            ),
            link=dict(
                source=self.source,
                target=self.target,
                value=self.values,
                color=self.colors,
                hovertemplate='%{source.label} → %{target.label}<br>Amount: $%{value:,.2f}<extra></extra>'
            ),
            arrangement='snap',
            orientation='h'
        )])
        
        fig.update_layout(
            title=dict(
                text="Income Flow: Income By Tags → Total Income → Total Expenses → Parent Categories → Categories",
                font=dict(size=16, color='#1f2937')
            ),
            font=dict(size=13, color='#1f2937', family='Arial, sans-serif'),
            height=700,
            paper_bgcolor='white',
            plot_bgcolor='white'
        )
        
        return fig
