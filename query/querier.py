import os
import vastdb
import pyarrow as pa
from dotenv import load_dotenv
from ibis import _
from pathlib import Path  # Import Path

def query_and_print(table, table_name: str, limit=5):
    """Executes a select query on a table and prints the results."""
    print("-" * 50)
    print(f"Querying first {limit} rows from '{table_name}' table...")
    
    try:
        # SELECT * FROM table LIMIT limit
        reader = table.select(limit_rows=limit)
        result_table = reader.read_all() # Returns a pyarrow.Table
        
        if result_table.num_rows > 0:
            print(f"✓ Found {result_table.num_rows} rows.")
            # Convert to Pandas DataFrame for easy printing
            df = result_table.to_pandas()
            print(df.to_string())
        else:
            print("  - No rows found.")
            
    except Exception as e:
        print(f"❌ Error querying '{table_name}': {e}")
    
    print("-" * 50)
    print()

def query_syslog_events(schema, limit=5):
    """Queries for syslog events in the 'events' table."""
    table_name = "events"
    print("-" * 50)
    print(f"Querying for syslog events from '{table_name}' table...")
    
    try:
        events_table = schema.table(table_name)
        
        # Use a predicate to filter for syslog events
        reader = events_table.select(
            predicate=(_.event_type == 'syslog'),
            limit_rows=limit
        )
        result_table = reader.read_all()
        
        if result_table.num_rows > 0:
            print(f"✓ Found {result_table.num_rows} syslog events.")
            df = result_table.to_pandas()
            print(df.to_string())
        else:
            print("  - No syslog events found.")
            
    except Exception as e:
        print(f"❌ Error querying syslog events: {e}")
    
    print("-" * 50)
    print()


def main():
    """Connects to VAST DB and queries the main observability tables."""
    # --- FIX: Load .env from the project root directory ---
    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(dotenv_path=env_path)
    
    # --- Configuration ---
    ENDPOINT = os.getenv("VAST_ENDPOINT")
    ACCESS_KEY = os.getenv("VAST_ACCESS_KEY")
    SECRET_KEY = os.getenv("VAST_SECRET_KEY")
    BUCKET_NAME = os.getenv("VAST_BUCKET")
    SCHEMA_NAME = os.getenv("VAST_SCHEMA")

    # --- Validation ---
    if not all([ENDPOINT, ACCESS_KEY, SECRET_KEY, BUCKET_NAME, SCHEMA_NAME]):
        print("❌ Error: Missing one or more required environment variables.")
        print(f"Attempted to load from: {env_path}")
        print("Please ensure the top-level .env file exists and is populated.")
        return

    print("Connecting to VAST Database...")
    print(f"  Endpoint: {ENDPOINT}")

    try:
        # --- Connection ---
        session = vastdb.connect(
            endpoint=ENDPOINT,
            access=ACCESS_KEY,
            secret=SECRET_KEY
        )

        with session.transaction() as tx:
            bucket = tx.bucket(BUCKET_NAME)
            schema = bucket.schema(SCHEMA_NAME)
            
            print(f"✓ Connection successful. Using bucket '{BUCKET_NAME}' and schema '{SCHEMA_NAME}'.\n")

            # --- Query Tables ---
            tables_to_query = ["events", "metrics", "entities"]
            for table_name in tables_to_query:
                try:
                    table = schema.table(table_name)
                    query_and_print(table, table_name)
                except Exception:
                    print(f"  - Table '{table_name}' not found in schema '{SCHEMA_NAME}'.")

            # --- Query Syslog Events ---
            query_syslog_events(schema)

    except Exception as e:
        print(f"❌ An error occurred during the database operation: {e}")

if __name__ == "__main__":
    main()