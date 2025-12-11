import re

BAN_WORDS = {"сво", "что-то", "пример"}

async def contains_banword(text: str | None) -> bool:
    if not text:
        return False

    text = text.lower()

    cleaned = re.sub(r"[^a-zа-я0-9ё]+", " ", text, flags=re.IGNORECASE)

    words = cleaned.split()

    # есть ли среди слов хоть одно бан-слово
    return any(bw in words for bw in BAN_WORDS)