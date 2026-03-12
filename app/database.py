import certifi
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.config import get_settings

settings = get_settings()

client: AsyncIOMotorClient = None
db: AsyncIOMotorDatabase = None


async def connect_to_mongo() -> None:
    """Create MongoDB connection on startup."""
    global client, db
    client = AsyncIOMotorClient(
        settings.MONGODB_URI,
        # Explicit TLS settings to be friendlier to hosted environments like Render
        tls=True,
        tlsAllowInvalidCertificates=True,
        serverSelectionTimeoutMS=15000,
    )
    db = client[settings.DATABASE_NAME]

    # Verify connectivity
    await client.admin.command("ping")
    print("\u2713 Connected to MongoDB")

    # Create indexes for users collection
    await db.users.create_index("username", unique=True)
    await db.users.create_index("email", unique=True)
    
    # Create indexes for test history
    await db.test_history.create_index("username")
    await db.test_history.create_index("test_id", unique=True)
    await db.test_history.create_index([("username", 1), ("completed_at", -1)])
    
    # Keep session index for active tests
    await db.user_sessions.create_index("session_id", unique=True)
    await db.user_sessions.create_index("username")


async def close_mongo_connection() -> None:
    """Close MongoDB connection on shutdown."""
    global client
    if client:
        client.close()


def get_database() -> AsyncIOMotorDatabase:
    """Return the database instance."""
    return db
