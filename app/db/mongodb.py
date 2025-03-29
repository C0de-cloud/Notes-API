from motor.motor_asyncio import AsyncIOMotorClient
from ..core.config import get_settings

settings = get_settings()

class MongoDB:
    client: AsyncIOMotorClient = None
    db = None

db = MongoDB()

async def connect_to_mongo():
    """Подключение к MongoDB и создание индексов"""
    db.client = AsyncIOMotorClient(settings.MONGODB_URL)
    db.db = db.client[settings.MONGODB_DB_NAME]
    
    # Создаем индексы для оптимизации запросов
    await db.db.users.create_index("email", unique=True)
    await db.db.users.create_index("username", unique=True)
    
    # Индексы для заметок
    await db.db.notes.create_index("owner_id")
    await db.db.notes.create_index("tags")
    await db.db.notes.create_index("created_at")
    await db.db.notes.create_index("updated_at")
    await db.db.notes.create_index([("title", "text"), ("content", "text")])
    
    # Индексы для тегов
    await db.db.tags.create_index("owner_id")
    await db.db.tags.create_index("name")
    
    # Индексы для коллекций
    await db.db.collections.create_index("owner_id")
    await db.db.collections.create_index("name")
    
    # Индексы для общего доступа
    await db.db.shared_notes.create_index([("note_id", 1), ("user_id", 1)], unique=True)

async def close_mongo_connection():
    """Закрытие соединения с MongoDB"""
    if db.client:
        db.client.close()

def get_database():
    """Получение базы данных MongoDB"""
    return db.db 