import json
from datetime import datetime, timezone
from aiohttp import web



ads = {}
next_id = 1


def json_response(data, status=200):
    """Вспомогательная функция для JSON-ответа с поддержкой кириллицы."""
    return web.Response(
        text=json.dumps(data, ensure_ascii=False),
        status=status,
        content_type="application/json",
    )


async def create_ad(request: web.Request) -> web.Response:
    """POST /ads — Создание нового объявления."""
    global next_id

    try:
        data = await request.json()
    except Exception:
        return json_response({"error": "Тело запроса должно быть в формате JSON"}, 400)

    if not data:
        return json_response({"error": "Тело запроса должно быть в формате JSON"}, 400)

    # Валидация обязательных полей
    required_fields = ['title', 'description', 'owner']
    for field in required_fields:
        if field not in data or not data[field]:
            return json_response(
                {"error": f"Поле '{field}' обязательно для заполнения"}, 400
            )

    new_ad = {
        "id": next_id,
        "title": data["title"],
        "description": data["description"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "owner": data["owner"],
    }

    ads[next_id] = new_ad
    next_id += 1

    return json_response(new_ad, 201)


async def get_ads(request: web.Request) -> web.Response:
    """GET /ads — Получение списка всех объявлений."""
    return json_response(list(ads.values()), 200)


async def get_ad(request: web.Request) -> web.Response:
    """GET /ads/{id} — Получение объявления по его ID."""
    ad_id = int(request.match_info['id'])
    ad = ads.get(ad_id)

    if ad is None:
        return json_response({"error": "Объявление не найдено"}, 404)

    return json_response(ad, 200)


async def update_ad(request: web.Request) -> web.Response:
    """PUT /ads/{id} — Редактирование объявления."""
    ad_id = int(request.match_info['id'])
    ad = ads.get(ad_id)

    if ad is None:
        return json_response({"error": "Объявление не найдено"}, 404)

    try:
        data = await request.json()
    except Exception:
        return json_response({"error": "Тело запроса должно быть в формате JSON"}, 400)

    if not data:
        return json_response({"error": "Тело запроса должно быть в формате JSON"}, 400)

    # Обновляем только переданные поля, дату создания не трогаем
    if 'title' in data:
        ad['title'] = data['title']
    if 'description' in data:
        ad['description'] = data['description']
    if 'owner' in data:
        ad['owner'] = data['owner']

    return json_response(ad, 200)


async def delete_ad(request: web.Request) -> web.Response:
    """DELETE /ads/{id} — Удаление объявления."""
    ad_id = int(request.match_info['id'])

    if ad_id not in ads:
        return json_response({"error": "Объявление не найдено"}, 404)

    del ads[ad_id]
    return json_response({"message": "Объявление успешно удалено"}, 200)


async def index(request: web.Request) -> web.Response:
    """GET / — Главная страница со списком эндпоинтов."""
    return json_response({
        "message": "API сайта объявлений (aiohttp)",
        "endpoints": {
            "POST   /ads": "Создать объявление",
            "GET    /ads": "Получить все объявления",
            "GET    /ads/{id}": "Получить объявление по ID",
            "PUT    /ads/{id}": "Редактировать объявление",
            "DELETE /ads/{id}": "Удалить объявление",
        },
    }, 200)


def create_app() -> web.Application:
    """Фабрика приложения: регистрирует маршруты."""
    app = web.Application()

    app.router.add_get('/', index)
    app.router.add_post('/ads', create_ad)
    app.router.add_get('/ads', get_ads)
    app.router.add_get('/ads/{id}', get_ad)
    app.router.add_put('/ads/{id}', update_ad)
    app.router.add_delete('/ads/{id}', delete_ad)

    return app


if __name__ == '__main__':
    app = create_app()
    web.run_app(app, host='127.0.0.1', port=5000)