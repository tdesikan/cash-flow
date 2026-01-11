"""Utility functions for formatting and text processing."""


def format_currency(amount):
    """Format currency with K/M suffixes for readability."""
    if abs(amount) >= 1000000:
        return f"${abs(amount)/1000000:.1f}M"
    elif abs(amount) >= 1000:
        return f"${abs(amount)/1000:.1f}K"
    else:
        return f"${abs(amount):,.0f}"


def truncate_label(label, max_length=25):
    """Truncate label if too long."""
    if len(label) > max_length:
        return label[:max_length-3] + "..."
    return label
