from app.core.database import engine
from sqlmodel import SQLModel
from app.models.vk_bot import VkBotAccount, VkBotSubscription, VkBotMessageLog

def create_tables():
    print("Starting table creation...")
    SQLModel.metadata.create_all(engine)
    print("VK Bot tables created successfully.")

if __name__ == "__main__":
    create_tables()
