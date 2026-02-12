# direct_atlas_migration.py
import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get MongoDB credentials
MONGO_DB = os.getenv("MONGO_DB")
MONGO_USER = os.getenv("MONGO_USER")
MONGO_PASS = os.getenv("MONGO_PASS")
MONGO_CLUSTER = os.getenv("MONGO_CLUSTER")

if not all([MONGO_DB, MONGO_USER, MONGO_PASS, MONGO_CLUSTER]):
    print("❌ Missing MongoDB environment variables")
    exit(1)

# Connect to MongoDB Atlas
connection_string = f"mongodb+srv://{MONGO_USER}:{MONGO_PASS}@{MONGO_CLUSTER}/{MONGO_DB}?retryWrites=true&w=majority"

try:
    client = MongoClient(connection_string)
    db = client[MONGO_DB]
    attendance_collection = db['attendance']
    
    print("✅ Connected to MongoDB Atlas successfully!")
    print(f"📊 Database: {MONGO_DB}\n")
    
    # Count documents without the field
    missing_field = attendance_collection.count_documents({'is_onWFH': {'$exists': False}})
    null_field = attendance_collection.count_documents({'is_onWFH': None})
    
    print(f"📊 Records without is_onWFH field: {missing_field}")
    print(f"📊 Records with null is_onWFH: {null_field}")
    print(f"📊 Total records to update: {missing_field + null_field}\n")
    
    if missing_field + null_field == 0:
        print("✅ All records already have the is_onWFH field!")
        exit(0)
    
    print("🔄 Starting migration...\n")
    
    # Update all documents without the field
    result1 = attendance_collection.update_many(
        {'is_onWFH': {'$exists': False}},
        {'$set': {'is_onWFH': False}}
    )
    
    # Update all documents with null value
    result2 = attendance_collection.update_many(
        {'is_onWFH': None},
        {'$set': {'is_onWFH': False}}
    )
    
    print("="*60)
    print("🎉 MIGRATION COMPLETED!")
    print("="*60)
    print(f"✅ Documents matched (missing field): {result1.matched_count}")
    print(f"✅ Documents updated (missing field): {result1.modified_count}")
    print(f"✅ Documents matched (null value): {result2.matched_count}")
    print(f"✅ Documents updated (null value): {result2.modified_count}")
    print(f"📊 Total updated: {result1.modified_count + result2.modified_count}")
    print("="*60)
    
    client.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()