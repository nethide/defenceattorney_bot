async def bots_plural(number: int) -> str:
    if number % 10 == 1 and number % 100 != 11:
        return f"{number} бот"
    elif 2 <= number % 10 <= 4 and (number % 100 < 10 or number % 100 >= 20):
        return f"{number} бота"
    else:
        return f"{number} ботов"