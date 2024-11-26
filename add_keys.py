import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

def add_key_to_db(collection, key_name, key_value):
    """Adds or updates a key in the MongoDB collection."""
    result = collection.update_one(
        {"name": key_name},
        {"$set": {"value": key_value}},
        upsert=True
    )
    if result.upserted_id:
        print(f"Key '{key_name}' added successfully.")
    else:
        print(f"Key '{key_name}' updated successfully.")

def main():
    # Connect to MongoDB
    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        print("Error: 'MONGO_URI' is not set in the environment variables.")
        return

    client = MongoClient(mongo_uri)
    db = client["R2D2BotDB"]
    keys_collection = db["keys"]

    print("Welcome to the Key Manager!")
    print("This script allows you to add or update keys in your database.")
    print("Type 'exit' to quit.\n")

    while True:
        key_name = input("Enter the key name (e.g., 'exchange_rate_api_key'): ").strip()
        if key_name.lower() == "exit":
            print("Exiting Key Manager. Goodbye!")
            break

        key_value = input(f"Enter the value for '{key_name}': ").strip()
        if key_value.lower() == "exit":
            print("Exiting Key Manager. Goodbye!")
            break

        add_key_to_db(keys_collection, key_name, key_value)

if __name__ == "__main__":
    main()
