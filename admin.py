import sqlite3
import sys

from shorten import DB_PATH


def list_reports():
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("""
        SELECT r.code, l.url, l.clicks, COUNT(*) AS n, MAX(r.created_at), GROUP_CONCAT(NULLIF(r.reason, ''), ' | ')
        FROM reports r JOIN links l ON l.code = r.code
        WHERE r.status = 'open' AND l.removed = 0
        GROUP BY r.code
        ORDER BY n DESC
    """).fetchall()
    conn.close()

    if not rows:
        print("No open reports.")
    for code, url, clicks, n, last, reasons in rows:
        print(f"{code}  ->  {url}")
        print(f"    {n} report(s), {clicks} click(s), latest {last}")
        if reasons:
            print(f"    reasons: {reasons}")


def remove(code):
    conn = sqlite3.connect(DB_PATH)
    changed = conn.execute("UPDATE links SET removed = 1 WHERE code = ?", (code,)).rowcount
    conn.execute("UPDATE reports SET status = 'actioned' WHERE code = ? AND status = 'open'", (code,))
    conn.commit()
    conn.close()
    print(f"Removed {code}." if changed else f"No link with code {code}.")


def dismiss(code):
    conn = sqlite3.connect(DB_PATH)
    changed = conn.execute("UPDATE reports SET status = 'dismissed' WHERE code = ? AND status = 'open'", (code,)).rowcount
    conn.commit()
    conn.close()
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
