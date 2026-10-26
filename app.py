import json
import aiosqlite
from datetime import datetime, timezone
from aiohttp import web

DB_PATH = "ads.db"


def json_response(data, status=200):
    """Вспомогательная функция для JSON-ответа с поддержкой кириллицы."""
    return web.Response(
        text=json.dumps(data, ensure_ascii=False),
        status=status,
        content_type="application/json",
    )


async def init_db(app: web.Application):
    """Инициализация БД при запуске приложения."""
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row  # Позволяет обращаться к колонкам по имени
    await db.execute("""
        CREATE TABLE IF NOT EXISTS ads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            owner TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    await db.commit()
    app['db'] = db


async def close_db(app: web.Application):
    """Закрытие соединения с БД при остановке приложения."""
    await app['db'].close()


async def create_ad(request: web.Request) -> web.Response:
    """POST /ads — Создание нового объявления."""
    try:
        data = await request.json()
    except Exception:
        return json_response({"error": "Тело запроса должно быть в формате JSON"}, 400)

    if not isinstance(data, dict) or not data:
        return json_response({"error": "Тело запроса должно быть в формате JSON"}, 400)

    required_fields = ['title', 'description', 'owner']
    for field in required_fields:
        if field not in data or not data[field]:
            return json_response({"error": f"Поле '{field}' обязательно для заполнения"}, 400)

    db = request.app['db']
    created_at = datetime.now(timezone.utc).isoformat()

    cursor = await db.execute(
        "INSERT INTO ads (title, description, owner, created_at) VALUES (?, ?, ?, ?)",
        (data['title'], data['description'], data['owner'], created_at)
    )
    await db.commit()
    ad_id = cursor.lastrowid

    cursor = await db.execute("SELECT * FROM ads WHERE id = ?", (ad_id,))
    row = await cursor.fetchone()

    return json_response(dict(row), 201)


async def get_ads(request: web.Request) -> web.Response:
    """GET /ads — Получение списка всех объявлений."""
    db = request.app['db']
    cursor = await db.execute("SELECT * FROM ads")
    rows = await cursor.fetchall()

    return json_response([dict(row) for row in rows], 200)


async def get_ad(request: web.Request) -> web.Response:
    """GET /ads/{id} — Получение объявления по его ID."""
    ad_id = int(request.match_info['id'])
    db = request.app['db']

    cursor = await db.execute("SELECT * FROM ads WHERE id = ?", (ad_id,))
    row = await cursor.fetchone()

    if row is None:
        return json_response({"error": "Объявление не найдено"}, 404)

    return json_response(dict(row), 200)


async def update_ad(request: web.Request) -> web.Response:
    """PUT /ads/{id} — Полное редактирование объявления (требует все поля)."""
    ad_id = int(request.match_info['id'])
    db = request.app['db']

    cursor = await db.execute("SELECT * FROM ads WHERE id = ?", (ad_id,))
    row = await cursor.fetchone()
    if row is None:
        return json_response({"error": "Объявление не найдено"}, 404)

    try:
        data = await request.json()
    except Exception:
        return json_response({"error": "Тело запроса должно быть в формате JSON"}, 400)

    if not isinstance(data, dict) or not data:
        return json_response({"error": "Тело запроса должно быть в формате JSON"}, 400)

    required_fields = ['title', 'description', 'owner']
    for field in required_fields:
        if field not in data or not data[field]:
            return json_response({"error": f"Поле '{field}' обязательно для заполнения"}, 400)

    await db.execute(
        "UPDATE ads SET title = ?, description = ?, owner = ? WHERE id = ?",
        (data['title'], data['description'], data['owner'], ad_id)
    )
    await db.commit()

    cursor = await db.execute("SELECT * FROM ads WHERE id = ?", (ad_id,))
    row = await cursor.fetchone()

    return json_response(dict(row), 200)


async def patch_ad(request: web.Request) -> web.Response:
    """PATCH /ads/{id} — Частичное редактирование объявления."""
    ad_id = int(request.match_info['id'])
    db = request.app['db']

    cursor = await db.execute("SELECT * FROM ads WHERE id = ?", (ad_id,))
    row = await cursor.fetchone()
    if row is None:
        return json_response({"error": "Объявление не найдено"}, 404)

    try:
        data = await request.json()
    except Exception:
        return json_response({"error": "Тело запроса должно быть в формате JSON"}, 400)

    if not isinstance(data, dict) or not data:
        return json_response({"error": "Тело запроса должно быть в формате JSON"}, 400)

    fields_to_update = []
    values = []
    allowed_fields = ['title', 'description', 'owner']

    for field in allowed_fields:
        if field in data:
            fields_to_update.append(f"{field} = ?")
            values.append(data[field])

    if not fields_to_update:
        return json_response({"error": "Не передано ни одного поля для обновления"}, 400)

    values.append(ad_id)
    query = f"UPDATE ads SET {', '.join(fields_to_update)} WHERE id = ?"

    await db.execute(query, values)
    await db.commit()

    cursor = await db.execute("SELECT * FROM ads WHERE id = ?", (ad_id,))
    row = await cursor.fetchone()

    return json_response(dict(row), 200)


async def delete_ad(request: web.Request) -> web.Response:
    """DELETE /ads/{id} — Удаление объявления."""
    ad_id = int(request.match_info['id'])
    db = request.app['db']

    cursor = await db.execute("SELECT * FROM ads WHERE id = ?", (ad_id,))
    row = await cursor.fetchone()
    if row is None:
        return json_response({"error": "Объявление не найдено"}, 404)

    await db.execute("DELETE FROM ads WHERE id = ?", (ad_id,))
    await db.commit()

    return json_response({"message": "Объявление успешно удалено"}, 200)


async def index(request: web.Request) -> web.Response:
    """GET / — Главная страница со списком эндпоинтов."""
    return json_response({
        "message": "API сайта объявлений (aiohttp + aiosqlite)",
        "endpoints": {
            "POST   /ads": "Создать объявление",
            "GET    /ads": "Получить все объявления",
            "GET    /ads/{id}": "Получить объявление по ID",
            "PUT    /ads/{id}": "Полностью редактировать объявление",
            "PATCH  /ads/{id}": "Частично редактировать объявление",
            "DELETE /ads/{id}": "Удалить объявление",
        },
    }, 200)


def create_app() -> web.Application:
    """Фабрика приложения: регистрирует маршруты и события жизненного цикла."""
    app = web.Application()

    # События жизненного цикла для БД
    app.on_startup.append(init_db)
    app.on_cleanup.append(close_db)

    # Маршруты
    app.router.add_get('/', index)
    app.router.add_post('/ads', create_ad)
    app.router.add_get('/ads', get_ads)
    app.router.add_get('/ads/{id}', get_ad)
    app.router.add_put('/ads/{id}', update_ad)
    app.router.add_patch('/ads/{id}', patch_ad)
    app.router.add_delete('/ads/{id}', delete_ad)

    return app


if __name__ == '__main__':
    app = create_app()
    web.run_app(app, host='127.0.0.1', port=5000)