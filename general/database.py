from pymongo import MongoClient
import certifi
import os
from dotenv import load_dotenv # Ensure dotenv is loaded for MONGO_URI

# Load environment variables immediately, before any other module that might use them
load_dotenv()

# --- MongoDB Client ---
MONGO_URI = os.getenv("MONGO_URI")
MONGO_EAGER_CONNECT = os.getenv("MONGO_EAGER_CONNECT", "false").lower() in ("1", "true", "yes")
MONGO_STRICT_STARTUP = os.getenv("MONGO_STRICT_STARTUP", "false").lower() in ("1", "true", "yes")

if not MONGO_URI:
    # CRITICAL: If MONGO_URI is not set, the app cannot proceed.
    # This will cause the app to crash immediately at import time.
    raise RuntimeError("CRITICAL: MONGO_URI environment variable is not set. Please check your .env file and ensure it's loaded.")

try:
    print("Attempting MongoDB connection...")
    client = MongoClient(
        MONGO_URI,
        tls=True,
        tlsCAFile=certifi.where(),
        serverSelectionTimeoutMS=5000 # Timeout for server selection
    )

    connected = False
    if MONGO_EAGER_CONNECT or MONGO_STRICT_STARTUP:
        # Force a connection check immediately to ensure client is usable
        client.admin.command('ping')
        connected = True
        print("SUCCESS: MongoDB client connected and verified.")
    else:
        print("INFO: Skipping eager MongoDB connection check (lazy mode).")

    db = client["jodettu"] # Assuming "jodettu" is your database name

    # --- Define Collections Eagerly ---
    # These are now real PyMongo Collection objects, initialized at import time.
    users = db.get_collection("users")
    own_animals = db.get_collection("own_animals")
    market_animals = db.get_collection("market_animals")
    machines = db.get_collection("machines")
    market = db.get_collection("marketplace")
    animal_types_collection = db.get_collection("animal_types")
    breeds_collection = db.get_collection("breeds")
    otp_collection = db.get_collection("otps")
    notifications_collection = db.get_collection("notifications")
    training_data_collection = db.get_collection("training_data")
    diseases_collection = db.get_collection("diseases")

    # --- Create Indexes ---
    # Attempt index creation if connected; otherwise skip with a warning.
    if connected:
        users.create_index("user_phone_number", unique=True)
        otp_collection.create_index("expires_at", expireAfterSeconds=0) # TTL index for OTP auto-expiry
        notifications_collection.create_index([("user_id", 1), ("created_at", -1)]) # Index for user notifications
        training_data_collection.create_index([("data_type", 1), ("animal_type", 1)]) # Index for training data
        print("SUCCESS: MongoDB collections and indexes initialized.")
    else:
        print("WARNING: MongoDB indexes not created (no eager connection).")

except Exception as e:
    print(f"ERROR: Failed to initialize MongoDB client or collections at import time: {e}")
    if MONGO_STRICT_STARTUP:
        # Re-raise to crash the app immediately if DB connection fails.
        # This ensures the app never runs in a broken state.
        raise e

# These functions are now empty as initialization is eager and happens at import time.
# They are kept for compatibility if other parts of the code still call them.
def init_db():
    pass

def setup_collections():
    pass
