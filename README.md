# Notes API

API для приложения заметок с поддержкой Markdown, тегов и совместного доступа.

## Функциональность

- Регистрация и авторизация пользователей
- Создание, редактирование и удаление заметок
- Поддержка Markdown в заметках
- Категоризация заметок через теги
- Поиск заметок по содержимому и тегам
- Общий доступ к заметкам с другими пользователями
- Создание коллекций заметок
- Экспорт заметок в различные форматы (PDF, HTML, Markdown)

## Технический стек

- Python 3.10+
- FastAPI 0.95+
- MongoDB (через Motor для асинхронной работы)
- Pydantic 2.0+
- JWT для аутентификации

## Установка и запуск

1. Клонировать репозиторий
2. Создать виртуальное окружение:
   ```
   python -m venv venv
   source venv/bin/activate  # для Linux/macOS
   venv\Scripts\activate     # для Windows
   ```
3. Установить зависимости:
   ```
   pip install -r requirements.txt
   ```
4. Создать файл `.env` на основе `.env.example`
5. Запустить MongoDB
6. Запустить приложение:
   ```
   python main.py
   ```

После запуска API будет доступно по адресу http://localhost:8000

## API Endpoints

### Аутентификация

- `POST /api/v1/auth/register` - Регистрация нового пользователя
- `POST /api/v1/auth/login` - Авторизация и получение JWT токена

### Пользователи

- `GET /api/v1/users/me` - Получение информации о текущем пользователе
- `PUT /api/v1/users/me` - Обновление информации о текущем пользователе

### Заметки

- `POST /api/v1/notes` - Создание новой заметки
- `GET /api/v1/notes` - Получение списка заметок с фильтрацией
- `GET /api/v1/notes/{note_id}` - Получение заметки по ID
- `PUT /api/v1/notes/{note_id}` - Обновление заметки
- `DELETE /api/v1/notes/{note_id}` - Удаление заметки
- `GET /api/v1/notes/search` - Поиск по заметкам

### Теги

- `GET /api/v1/tags` - Получение списка всех тегов пользователя
- `GET /api/v1/tags/{tag_name}/notes` - Получение всех заметок с указанным тегом

### Коллекции

- `POST /api/v1/collections` - Создание новой коллекции
- `GET /api/v1/collections` - Получение списка коллекций
- `GET /api/v1/collections/{collection_id}` - Получение коллекции по ID
- `PUT /api/v1/collections/{collection_id}` - Обновление коллекции
- `DELETE /api/v1/collections/{collection_id}` - Удаление коллекции
- `POST /api/v1/collections/{collection_id}/notes/{note_id}` - Добавление заметки в коллекцию
- `DELETE /api/v1/collections/{collection_id}/notes/{note_id}` - Удаление заметки из коллекции

### Общий доступ

- `POST /api/v1/notes/{note_id}/share` - Предоставление доступа к заметке другому пользователю
- `GET /api/v1/notes/shared-with-me` - Получение заметок, к которым предоставлен доступ
- `DELETE /api/v1/notes/{note_id}/share/{user_id}` - Отмена доступа к заметке

### Экспорт

- `GET /api/v1/notes/{note_id}/export/{format}` - Экспорт заметки в указанном формате
- `GET /api/v1/collections/{collection_id}/export/{format}` - Экспорт коллекции в указанном формате

## Примеры запросов

### Создание заметки

```
POST /api/v1/notes
{
  "title": "Моя первая заметка",
  "content": "# Заголовок\n\nЭто *заметка* с **форматированием** в Markdown.",
  "color": "#f5f5dc",
  "tags": ["важное", "идеи"]
}
```

### Поиск заметок

```
GET /api/v1/notes/search?query=важное&tags=идеи
```

### Предоставление доступа к заметке

```
POST /api/v1/notes/123/share
{
  "user_id": "5f9d7a3b4e5c2d1a8b7c6d5e",
  "permission": "read"
}
```
