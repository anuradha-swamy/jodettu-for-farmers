import os 
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING
load_dotenv()
"""
This module initializes the database and creates collections for own animals, market animals, machines, and users.
"""
MONGO_URI=os.getenv("MONGO_URI")
ANIMALS=os.getenv("ANIMALS")
OWN_ANIMALS=os.getenv("OWN_ANIMALS")
MARKET_ANIMALS=os.getenv("MARKET_ANIMALS")
MACHINES=os.getenv("MACHINES")
MARKET=os.getenv("MARKET")
USERS=os.getenv("USER")
ANIMAL_TYPES=os.getenv("ANIMAL_TYPES", "animal_types")
BREEDS=os.getenv("BREEDS", "breeds")

# Lazy database connection - will be initialized on first use
client = None
db = None
own_animals = None
market_animals = None
machines = None
market = None
users = None
animal_types_collection = None
breeds_collection = None

def get_db():
    """Get database connection - lazy initialization"""
    global client, db, own_animals, market_animals, machines, market, users, animal_types_collection, breeds_collection
    
    if client is None:
        print("🔄 Initializing database connection...")
        client = AsyncIOMotorClient(MONGO_URI, serverSelectionTimeoutMS=5000)  # 5 second timeout
        db = client[ANIMALS]
        own_animals = db[OWN_ANIMALS]
        market_animals = db[MARKET_ANIMALS]
        machines = db[MACHINES]
        market = db[MARKET]
        users = db[USERS]
        animal_types_collection = db[ANIMAL_TYPES]
        breeds_collection = db[BREEDS]
        print("✅ Database connection established.")
    
    return db

async def init_db():
    """Initialize database collections - now with lazy connection"""
    UPLOAD_FILES="upload_files"
    os.makedirs(UPLOAD_FILES,exist_ok=True)
    
    # Get database connection
    db = get_db()
    existing_collections=await db.list_collection_names()
    
    async def create_collection_with_counter(collection):
        """
        Create a collection with an ID counter if it doesn't exist.
        """
        if collection not in existing_collections:
            await db.create_collection(collection)
            await db[collection].insert_one({"function":"ID_counter","count":1})

    
    await create_collection_with_counter(OWN_ANIMALS)
    await create_collection_with_counter(MARKET_ANIMALS)
    await create_collection_with_counter(MACHINES)
    await create_collection_with_counter(USERS)

    if MARKET not in existing_collections:
        await db.create_collection(MARKET)
        await market.insert_one({"function":"ID_counter","med_count":1,"feed_count":1})

    if ANIMAL_TYPES not in existing_collections:
        await db.create_collection(ANIMAL_TYPES)
        await animal_types_collection.insert_many([
            {"type": "Cow"},
            {"type": "Sheep"},
            {"type": "Goat"}
        ])

    if BREEDS not in existing_collections:
        await db.create_collection(BREEDS)
        await breeds_collection.insert_many([
            {"type": "Cow", "breed": "Holstein"},
            {"type": "Cow", "breed": "Jersey"},
            {"type": "Sheep", "breed": "Merino"},
            {"type": "Sheep", "breed": "Suffolk"},
            {"type": "Goat", "breed": "Boer"},
            {"type": "Goat", "breed": "Nubian"}
        ])
    
    """
    Create indexes for the collections to ensure unique constraints on the specified fields.
    """
    await own_animals.create_index([("own_animal_id",ASCENDING)],unique=True)
    await market_animals.create_index([("market_animal_id",ASCENDING)],unique=True)
    await machines.create_index([("machine_id",ASCENDING)],unique=True)
    await market.create_index([("id",ASCENDING)],unique=True, sparse=True)
