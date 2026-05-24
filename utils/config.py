import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

db_config = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_DATABASE', 'default_db'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'port': int(os.getenv('DB_PORT', 3306))
}
