from pymongo import MongoClient
from .config import settings

client = MongoClient(settings.MONGO_URL)
db = client['messenger_db']

def get_user_collection():
    return db['users']

def get_chat_collection():
    return db['chats']
