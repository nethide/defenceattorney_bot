import re

async def parse_duration_one(token: str) -> int:
    token = token.strip().lower()
    match = re.fullmatch(r"(\d+)\s*([dhm])", token)
    if not match:
        raise ValueError(f"Неверный формат: {token}")

    value = int(match.group(1))
    unit = match.group(2)

    multipliers = {
        "d": 24 * 60 * 60,
        "h": 60 * 60,
        "m": 60,
    }

    return value * multipliers[unit]