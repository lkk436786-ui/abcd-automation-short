from __future__ import annotations

from datetime import date, datetime, timedelta
import hashlib
from pathlib import Path
from zoneinfo import ZoneInfo

from .history import read_json


LONG_VIDEO_SLOTS_IST = ((4, 17), (5, 17), (6, 17), (10, 47), (11, 47), (12, 47), (15, 38), (16, 38), (17, 38))


def _uploaded_count(history: dict, day: str) -> int:
    return sum(1 for item in history.get("shorts", []) if item.get("date") == day and item.get("status") == "uploaded")


def _uploaded_count_from_batch(root: Path, day: str) -> int:
    for path in (root / ".shorts_work").glob("daily_batch_*.json"):
        data = read_json(path, {})
        if data.get("date") == day:
            return sum(1 for status in data.get("status", {}).values() if status.get("status") == "uploaded")
    return 0


def _pending_batch_days(root: Path, today: date) -> list[str]:
    pending: list[str] = []
    for path in sorted((root / ".shorts_work").glob("daily_batch_*.json")):
        data = read_json(path, {})
        value = data.get("date")
        if not value:
            continue
        try:
            day = date.fromisoformat(value)
        except ValueError:
            continue
        if today - timedelta(days=2) <= day <= today and sum(1 for status in data.get("status", {}).values() if status.get("status") == "uploaded") < 5:
            pending.append(value)
    return pending


def main() -> int:
    now = datetime.now(ZoneInfo("Asia/Kolkata"))
    today = now.date()
    today_key = today.isoformat()
    history = read_json(Path(".shorts_work") / "upload_history.json", {"shorts": []})
    uploaded_today = max(_uploaded_count(history, today_key), _uploaded_count_from_batch(Path("."), today_key))
    pending = _pending_batch_days(Path("."), today)
    if pending:
        run_date = min(pending)
        should_run = True
        target_hour = now.hour
        target_minute = now.minute
    else:
        # Match the long-video workflow's publishing slots. Keep one selected
        # slot stable for the whole day so retries do not create duplicates.
        target_hour, target_minute = LONG_VIDEO_SLOTS_IST[int(hashlib.sha256(today_key.encode()).hexdigest()[:8], 16) % len(LONG_VIDEO_SLOTS_IST)]
        run_date = today_key
        should_run = (now.hour, now.minute) >= (target_hour, target_minute) and uploaded_today < 5
    print(f"run={'true' if should_run else 'false'}")
    print(f"run_date={run_date}")
    print(f"target_hour_ist={target_hour:02d}:{target_minute:02d}")
    print(f"uploaded_today={uploaded_today}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
