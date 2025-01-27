from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pymongo
import os
from dotenv import load_dotenv
from scalar_fastapi import get_scalar_api_reference

app = FastAPI()

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
if not MONGODB_URI:
    raise ValueError("MONGODB_URI environment variable not set")

try:
    client = pymongo.MongoClient(MONGODB_URI)
    db = client["test_db"]
    collection = db["items"]
    client.admin.command('ping')
    print("Connected to MongoDB")
except pymongo.errors.ConnectionFailure as e:
    print(f"Could not connect to MongoDB: {e}")
    exit()

except pymongo.errors.ServerSelectionTimeoutError as e:
    print(f"Connection timed out: {e}")
    exit()

except Exception as e:
    print(f"An unexpected error occurred during connection: {e}")
    exit()


class Item(BaseModel):
    name: str
    description: str | None = None

@app.get("/")
async def root():
    return {"message": "Hello from FastAPI and MongoDB!"}

@app.get("/scalar", include_in_schema=False)
async def scalar_html():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title=app.title,
    )

@app.post("/items/", response_model=Item, status_code=201)
async def create_item(item: Item):
    try:
        result = collection.insert_one(item.dict())
        inserted_item = collection.find_one({"_id": result.inserted_id})
        return Item(**inserted_item)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating item: {e}")

@app.get("/items/{item_name}", response_model=Item)
async def read_item(item_name: str):
    item = collection.find_one({"name": item_name})
    if item:
        return Item(**item)
    raise HTTPException(status_code=404, detail="Item not found")


@app.get("/items/", response_model=list[Item])
async def list_items():
    items = list(collection.find())
    return [Item(**item) for item in items]


@app.delete("/items/{item_name}")
async def delete_item(item_name: str):
    result = collection.delete_one({"name": item_name})
    if result.deleted_count == 1:
        return {"message": "Item deleted"}
    raise HTTPException(status_code=404, detail="Item not found")