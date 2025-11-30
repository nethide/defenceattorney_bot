async def members_plural(number: int) -> str:
    if number % 10 == 1 and number % 100 != 11:
        return f"{number} участник"
    elif 2 <= number % 10 <= 4 and (number % 100 < 10 or number % 100 >= 20):
        return f"{number} участника"
    else:
        return f"{number} участников"