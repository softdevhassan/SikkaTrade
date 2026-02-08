def should_close(entry_price, current_price, tp, sl):
    change_pct = ((current_price - entry_price) / entry_price) * 100

    if change_pct >= tp:
        return True, change_pct
    if change_pct <= -sl:
        return True, change_pct

    return False, change_pct
