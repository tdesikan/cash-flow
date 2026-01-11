"""Color palette functions for Sankey diagram visualization."""
import colorsys


def generate_category_colors(n, saturation=0.7, lightness=0.6):
    """Generate distinct colors using HSL color space."""
    colors = []
    for i in range(n):
        hue = (i * 360 / n) % 360
        rgb = colorsys.hls_to_rgb(hue / 360, lightness, saturation)
        colors.append(f"rgba({int(rgb[0]*255)}, {int(rgb[1]*255)}, {int(rgb[2]*255)}, 0.6)")
    return colors


def get_income_color(alpha=0.6):
    """Green shades for income."""
    return f"rgba(34, 197, 94, {alpha})"  # Modern green


def get_savings_color(alpha=0.6):
    """Blue for savings."""
    return f"rgba(59, 130, 246, {alpha})"  # Modern blue


def get_income_node_color(alpha=0.8):
    """Darker green for income nodes."""
    return f"rgba(22, 163, 74, {alpha})"


def get_income_tag_colors(count):
    """Get color palette for income tags."""
    return [
        "rgba(34, 197, 94, 0.85)",   # Bright green
        "rgba(22, 163, 74, 0.85)",   # Medium green
        "rgba(21, 128, 61, 0.85)",   # Darker green
        "rgba(20, 83, 45, 0.85)",    # Dark green
    ]
