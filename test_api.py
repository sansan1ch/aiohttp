import asyncio
import aiohttp


async def main():
    base_url = "http://127.0.0.1:5000"

    async with aiohttp.ClientSession() as session:
        # 1. Создать объявление
        print("=== Создание объявления ===")
        async with session.post(
            f"{base_url}/ads",
            json={"title": "Продам велосипед", "description": "Новый", "owner": "Иван"}
        ) as resp:
            print(f"Status: {resp.status}")
            print(await resp.json(content_type=None))

        # 2. Создать второе объявление
        async with session.post(
            f"{base_url}/ads",
            json={"title": "Продам ноутбук", "description": "Игровой", "owner": "Пётр"}
        ) as resp:
            print(f"\nStatus: {resp.status}")
            print(await resp.json(content_type=None))

        # 3. Получить все объявления
        print("\n=== Все объявления ===")
        async with session.get(f"{base_url}/ads") as resp:
            print(f"Status: {resp.status}")
            print(await resp.json(content_type=None))

        # 4. Получить одно объявление
        print("\n=== Объявление #1 ===")
        async with session.get(f"{base_url}/ads/1") as resp:
            print(f"Status: {resp.status}")
            print(await resp.json(content_type=None))

        # 5. Редактировать
        print("\n=== Редактирование ===")
        async with session.put(
            f"{base_url}/ads/1",
            json={"title": "Продам горный велосипед"}
        ) as resp:
            print(f"Status: {resp.status}")
            print(await resp.json(content_type=None))

        # 6. Удалить
        print("\n=== Удаление ===")
        async with session.delete(f"{base_url}/ads/2") as resp:
            print(f"Status: {resp.status}")
            print(await resp.json(content_type=None))

        # 7. Проверка после удаления
        print("\n=== После удаления ===")
        async with session.get(f"{base_url}/ads") as resp:
            print(f"Status: {resp.status}")
            print(await resp.json(content_type=None))


if __name__ == '__main__':
    asyncio.run(main())