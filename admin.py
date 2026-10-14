import sys

from shorten import get_conn


def list_reports():
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT r.code, l.url, l.clicks, COUNT(*) AS n, MAX(r.created_at), string_agg(NULLIF(r.reason, ''), ' | ')
            FROM reports r JOIN links l ON l.code = r.code
            WHERE r.status = 'open' AND l.removed = 0
            GROUP BY r.code, l.url, l.clicks
            ORDER BY n DESC
        """).fetchall()

    if not rows:
        print("No open reports.")
    for code, url, clicks, n, last, reasons in rows:
        print(f"{code}  ->  {url}")
        print(f"    {n} report(s), {clicks} click(s), latest {last:%Y-%m-%d %H:%M}")
        if reasons:
            print(f"    reasons: {reasons}")


def remove(code):
    with get_conn() as conn:
        changed = conn.execute("UPDATE links SET removed = 1 WHERE code = %s", (code,)).rowcount
        conn.execute("UPDATE reports SET status = 'actioned' WHERE code = %s AND status = 'open'", (code,))
    print(f"Removed {code}." if changed else f"No link with code {code}.")


def dismiss(code):
    with get_conn() as conn:
        changed = conn.execute("UPDATE reports SET status = 'dismissed' WHERE code = %s AND status = 'open'", (code,)).rowcount
    print(f"Dismissed {changed} report(s) for {code}.")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args == ["reports"]:
        list_reports()
    elif len(args) == 2 and args[0] == "remove":
        remove(args[1])
    elif len(args) == 2 and args[0] == "dismiss":
        dismiss(args[1])
    else:
        print("Usage:\n  python admin.py reports\n  python admin.py remove <code>\n  python admin.py dismiss <code>")
