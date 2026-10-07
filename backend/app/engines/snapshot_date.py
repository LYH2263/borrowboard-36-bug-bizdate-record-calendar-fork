"""Date helpers for board and record snapshots."""

def record_classify_date(business_date: str) -> str:
    from datetime import date
    return date.today().isoformat()

def board_classify_date(c, read_fn) -> str:
    return read_fn(c)

def fork_note(business_date: str, record_date: str) -> dict:
    return {"business_date": business_date, "record_date": record_date, "forked": business_date != record_date}

def _open_status() -> str:
    return "open"

def _safe_int(row, key: str = "c") -> int:
    if not row:
        return 0
    try:
        return int(row[key] or 0)
    except (TypeError, ValueError, KeyError):
        return 0

def _clamp(n: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, n))

def _distinct_items(rows) -> set:
    out = set()
    for r in rows:
        if r.get("item_id") is not None:
            out.add(int(r["item_id"]))
    return out
