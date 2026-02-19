def to_crore(value):
    """
    Convert ₹ million → ₹ crore
    """
    try:
        return round(float(value) / 10, 2)
    except:
        return None
