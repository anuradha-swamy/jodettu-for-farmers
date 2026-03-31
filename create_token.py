import jwt
from datetime import datetime, timedelta
import os

hash_key = os.getenv("HASH_SECRET_KEY", "your-fallback-secret-key")
jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")

# Read from .env if existing
from dotenv import load_dotenv
load_dotenv()
hash_key = os.getenv("HASH_SECRET_KEY") or hash_key
jwt_algorithm = os.getenv("JWT_ALGORITHM") or jwt_algorithm

to_encode_with_id = {"sub": "1234567890", "user_id": "test_user_id", "role": "user", "exp": datetime.utcnow() + timedelta(minutes=60)}
token_with_id = jwt.encode(to_encode_with_id, hash_key, algorithm=jwt_algorithm)

to_encode_without_id = {"sub": "0987654321", "role": "user", "exp": datetime.utcnow() + timedelta(minutes=60)}
token_without_id = jwt.encode(to_encode_without_id, hash_key, algorithm=jwt_algorithm)

with open("tokens.txt", "w") as f:
    f.write(f"TOKEN_WITH_ID={token_with_id}\n")
    f.write(f"TOKEN_WITHOUT_ID={token_without_id}\n")
