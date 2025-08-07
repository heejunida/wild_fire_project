import oracledb
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize Oracle Instant Client
try:
    oracledb.init_oracle_client()
except oracledb.DatabaseError as e:
    print(f"Could not initialize Oracle Client. Check your Instant Client installation and path. Error: {e}")
    # You might want to exit or handle this more gracefully depending on your application's needs
    pass

def get_db_connection():
    try:
        conn = oracledb.connect(
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            dsn=f"{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_SID')}"
        )
        return conn
    except oracledb.DatabaseError as e:
        print(f"Error connecting to database: {e}")
        return None
