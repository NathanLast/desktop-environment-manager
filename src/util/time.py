from datetime import datetime


def get_now_millis() -> int:
    return int(datetime.now().timestamp() * 1000)


def millis_to_datetime_str(timestamp: int) -> str:
    return datetime.fromtimestamp(timestamp / 1000).strftime("%Y-%m-%d %H:%M:%S")
