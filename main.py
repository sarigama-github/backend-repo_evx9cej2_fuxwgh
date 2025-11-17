import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Game

app = FastAPI(title="Games Download API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Games Download API is running"}

@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
            
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    
    import os as _os
    response["database_url"] = "✅ Set" if _os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if _os.getenv("DATABASE_NAME") else "❌ Not Set"
    
    return response

# -----------------------
# Games endpoints
# -----------------------

class CreateGameRequest(Game):
    pass

class GameOut(Game):
    id: str

@app.post("/api/games", response_model=dict)
async def create_game(payload: CreateGameRequest):
    try:
        new_id = create_document("game", payload)
        return {"id": new_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/games", response_model=List[GameOut])
async def list_games(q: Optional[str] = None, limit: int = 50):
    try:
        filter_dict = {}
        if q:
            # Simple text filter on title or genre
            filter_dict = {"$or": [
                {"title": {"$regex": q, "$options": "i"}},
                {"genre": {"$regex": q, "$options": "i"}},
            ]}
        docs = get_documents("game", filter_dict=filter_dict, limit=limit)
        out: List[GameOut] = []
        for d in docs:
            d["id"] = str(d.get("_id"))
            d.pop("_id", None)
            out.append(GameOut(**d))
        return out
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/games/sample", response_model=List[GameOut])
async def seed_sample_games():
    """Create a few sample games if collection is empty and return them."""
    try:
        existing = get_documents("game", limit=1)
        if not existing:
            samples = [
                Game(
                    title="Starlight Odyssey",
                    description="Explore a vast galaxy in this open-world space adventure.",
                    genre="Adventure",
                    platform="PC",
                    size_gb=12.5,
                    thumbnail="https://images.unsplash.com/photo-1586125674857-4c4a1b3e72d0",
                    screenshots=[
                        "https://images.unsplash.com/photo-1542751110-97427bbecf20",
                        "https://images.unsplash.com/photo-1542831371-29b0f74f9713",
                    ],
                    download_url="https://example.com/download/starlight-odyssey"
                ),
                Game(
                    title="Neon Drift",
                    description="High-speed neon-soaked racing in a cyberpunk city.",
                    genre="Racing",
                    platform="PC",
                    size_gb=8.2,
                    thumbnail="https://images.unsplash.com/photo-1511512578047-dfb367046420",
                    screenshots=[
                        "https://images.unsplash.com/photo-1535223289827-42f1e9919769",
                        "https://images.unsplash.com/photo-1483721310020-03333e577078",
                    ],
                    download_url="https://example.com/download/neon-drift"
                ),
                Game(
                    title="Echoes of Eldoria",
                    description="A story-driven RPG with tactical combat and rich lore.",
                    genre="RPG",
                    platform="PC",
                    size_gb=25.0,
                    thumbnail="https://images.unsplash.com/photo-1520975922371-24b89f8378fd",
                    screenshots=[
                        "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab",
                    ],
                    download_url="https://example.com/download/echoes-of-eldoria"
                ),
            ]
            for g in samples:
                create_document("game", g)
        docs = get_documents("game", limit=50)
        out: List[GameOut] = []
        for d in docs:
            d["id"] = str(d.get("_id"))
            d.pop("_id", None)
            out.append(GameOut(**d))
        return out
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
