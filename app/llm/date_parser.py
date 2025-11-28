# date_parser.py
import re
from datetime import datetime, timedelta, date
from typing import Optional, Tuple

# YYYY-MM-DD 정규식
DATE_PATTERN = re.compile(r"(20\d{2}-\d{2}-\d{2})")


# ===== 오늘 날짜 텍스트 =====
def get_today_context() -> Tuple[str, str]:
    now = datetime.now()
    today_iso = now.strftime("%Y-%m-%d")
    weekday = ["월", "화", "수", "목", "금", "토", "일"][now.weekday()]
    return today_iso, weekday


# ===== 파일명에서 날짜 추출 =====
def extract_date_from_path(path: str) -> Optional[date]:
    name = path.replace("\\", "/").split("/")[-1]
    m = DATE_PATTERN.search(name)
    if not m:
        return None
    return datetime.strptime(m.group(1), "%Y-%m-%d").date()


# ===== 자연어 날짜 파싱 =====
def detect_date_range_from_query(query: str) -> Tuple[Optional[date], Optional[date]]:
    q = query.replace(" ", "")
    today = date.today()

    # YYYY-MM-DD 직접 입력
    m = DATE_PATTERN.search(q)
    if m:
        d = datetime.strptime(m.group(1), "%Y-%m-%d").date()
        return d, d

    # 오늘 / 내일 / 모레
    if "오늘" in q: return today, today
    if "내일" in q: return today + timedelta(days=1), today + timedelta(days=1)
    if "모레" in q: return today + timedelta(days=2), today + timedelta(days=2)

    # N일 뒤 / 후 / 전
    m = re.search(r"(\d+)일(뒤|후)", q)
    if m:
        t = today + timedelta(days=int(m.group(1)))
        return t, t
    m = re.search(r"(\d+)일전", q)
    if m:
        t = today - timedelta(days=int(m.group(1)))
        return t, t

    # 이번주
    if "이번주" in q:
        monday = today - timedelta(days=today.weekday())
        return monday, monday + timedelta(days=6)

    # 다음주
    if "다음주" in q:
        monday = today - timedelta(days=today.weekday())
        nm = monday + timedelta(weeks=1)
        return nm, nm + timedelta(days=6)

    # 다다음주
    if "다다음주" in q:
        monday = today - timedelta(days=today.weekday())
        nm = monday + timedelta(weeks=2)
        return nm, nm + timedelta(days=6)

    # 이번주 주말
    if "이번주주말" in q:
        monday = today - timedelta(days=today.weekday())
        return monday + timedelta(days=5), monday + timedelta(days=6)

    # 다음주 주말
    if "다음주주말" in q:
        monday = today - timedelta(days=today.weekday())
        nm = monday + timedelta(weeks=1)
        return nm + timedelta(days=5), nm + timedelta(days=6)

    # 이번달
    if "이번달" in q:
        start = today.replace(day=1)
        if today.month == 12:
            end = date(today.year + 1, 1, 1) - timedelta(days=1)
        else:
            end = date(today.year, today.month + 1, 1) - timedelta(days=1)
        return start, end

    # 다음달
    if "다음달" in q:
        if today.month == 12:
            start = date(today.year + 1, 1, 1)
        else:
            start = date(today.year, today.month + 1, 1)
        if start.month == 12:
            end = date(start.year + 1, 1, 1) - timedelta(days=1)
        else:
            end = date(start.year, start.month + 1, 1) - timedelta(days=1)
        return start, end

    # 평일
    if "평일" in q:
        monday = today - timedelta(days=today.weekday())
        return monday, monday + timedelta(days=4)

    # 주말
    if "주말" in q:
        monday = today - timedelta(days=today.weekday())
        return monday + timedelta(days=5), monday + timedelta(days=6)

    return None, None
