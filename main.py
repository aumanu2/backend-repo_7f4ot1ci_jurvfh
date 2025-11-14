import os
from typing import List, Optional, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Profile, Project, Endorsement

app = FastAPI(title="Networking App API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Helpers ----------

def serialize_doc(doc: dict) -> dict:
    if not doc:
        return doc
    d = dict(doc)
    _id = d.get("_id")
    if isinstance(_id, ObjectId):
        d["id"] = str(_id)
        del d["_id"]
    return d


def get_collection_name(model_cls: Any) -> str:
    return model_cls.__name__.lower()


# ---------- Health & Schema ----------

@app.get("/")
def root():
    return {"message": "Networking App Backend is running"}


@app.get("/api/health")
def health():
    try:
        ok = db is not None and isinstance(db.list_collection_names(), list)
        return {"ok": True, "database": "connected" if ok else "not_connected"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.get("/schema")
def get_schema():
    # Expose JSON schema for key models (useful for tooling/viewers)
    return {
        "profile": Profile.model_json_schema(),
        "project": Project.model_json_schema(),
        "endorsement": Endorsement.model_json_schema(),
    }


# ---------- Profiles ----------

class ProfileCreate(Profile):
    pass


class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    headline: Optional[str] = None
    bio: Optional[str] = None
    skills: Optional[List[str]] = None
    interests: Optional[List[str]] = None
    timezone: Optional[str] = None
    availability: Optional[str] = None
    goals: Optional[str] = None
    links: Optional[List[str]] = None
    verified: Optional[bool] = None


@app.post("/api/profiles")
def create_profile(payload: ProfileCreate):
    try:
        # Check existing by email
        existing = db[get_collection_name(Profile)].find_one({"email": payload.email})
        if existing:
            raise HTTPException(status_code=409, detail="Profile with this email already exists")
        inserted_id = create_document(get_collection_name(Profile), payload)
        doc = db[get_collection_name(Profile)].find_one({"_id": ObjectId(inserted_id)})
        return serialize_doc(doc)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/profiles")
def list_profiles(email: Optional[str] = None, q: Optional[str] = None, limit: int = 25):
    filt = {}
    if email:
        filt["email"] = email
    if q:
        # simple text search on name/headline/skills
        filt["$or"] = [
            {"name": {"$regex": q, "$options": "i"}},
            {"headline": {"$regex": q, "$options": "i"}},
            {"skills": {"$elemMatch": {"$regex": q, "$options": "i"}}},
        ]
    docs = get_documents(get_collection_name(Profile), filt, limit=limit)
    return [serialize_doc(d) for d in docs]


@app.get("/api/profiles/{profile_id}")
def get_profile(profile_id: str):
    try:
        doc = db[get_collection_name(Profile)].find_one({"_id": ObjectId(profile_id)})
        if not doc:
            raise HTTPException(status_code=404, detail="Profile not found")
        return serialize_doc(doc)
    except Exception:
        raise HTTPException(status_code=404, detail="Profile not found")


@app.put("/api/profiles/{profile_id}")
def update_profile(profile_id: str, payload: ProfileUpdate):
    try:
        update_data = {k: v for k, v in payload.model_dump(exclude_none=True).items()}
        if not update_data:
            return {"updated": False}
        res = db[get_collection_name(Profile)].update_one(
            {"_id": ObjectId(profile_id)}, {"$set": update_data}
        )
        if res.matched_count == 0:
            raise HTTPException(status_code=404, detail="Profile not found")
        doc = db[get_collection_name(Profile)].find_one({"_id": ObjectId(profile_id)})
        return serialize_doc(doc)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------- Projects ----------

class ProjectCreate(Project):
    pass


class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    brief: Optional[str] = None
    tags: Optional[List[str]] = None
    roles_needed: Optional[List[str]] = None
    status: Optional[str] = None
    visibility: Optional[str] = None


@app.post("/api/projects")
def create_project(payload: ProjectCreate):
    try:
        inserted_id = create_document(get_collection_name(Project), payload)
        doc = db[get_collection_name(Project)].find_one({"_id": ObjectId(inserted_id)})
        return serialize_doc(doc)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/projects")
def list_projects(owner_id: Optional[str] = None, q: Optional[str] = None, limit: int = 50):
    filt: dict = {}
    if owner_id:
        filt["owner_id"] = owner_id
    if q:
        filt["$or"] = [
            {"title": {"$regex": q, "$options": "i"}},
            {"brief": {"$regex": q, "$options": "i"}},
            {"tags": {"$elemMatch": {"$regex": q, "$options": "i"}}},
        ]
    docs = get_documents(get_collection_name(Project), filt, limit=limit)
    return [serialize_doc(d) for d in docs]


@app.get("/api/projects/{project_id}")
def get_project(project_id: str):
    try:
        doc = db[get_collection_name(Project)].find_one({"_id": ObjectId(project_id)})
        if not doc:
            raise HTTPException(status_code=404, detail="Project not found")
        return serialize_doc(doc)
    except Exception:
        raise HTTPException(status_code=404, detail="Project not found")


@app.put("/api/projects/{project_id}")
def update_project(project_id: str, payload: ProjectUpdate):
    try:
        update_data = {k: v for k, v in payload.model_dump(exclude_none=True).items()}
        if not update_data:
            return {"updated": False}
        res = db[get_collection_name(Project)].update_one(
            {"_id": ObjectId(project_id)}, {"$set": update_data}
        )
        if res.matched_count == 0:
            raise HTTPException(status_code=404, detail="Project not found")
        doc = db[get_collection_name(Project)].find_one({"_id": ObjectId(project_id)})
        return serialize_doc(doc)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------- Simple Matchmaking ----------

class MatchRequest(BaseModel):
    profile_id: Optional[str] = None
    goals: Optional[str] = None
    skills: Optional[List[str]] = None
    interests: Optional[List[str]] = None
    limit: int = 10


@app.post("/api/matches")
def get_matches(payload: MatchRequest):
    """Very simple heuristic: score users by shared interests + complementary skills.
    If profile_id provided, start from that user's profile.
    """
    try:
        base_profile: Optional[dict] = None
        if payload.profile_id:
            base_profile = db[get_collection_name(Profile)].find_one({"_id": ObjectId(payload.profile_id)})
        if base_profile:
            base_skills = set(base_profile.get("skills", []))
            base_interests = set(base_profile.get("interests", []))
        else:
            base_skills = set(payload.skills or [])
            base_interests = set(payload.interests or [])

        candidates = list(db[get_collection_name(Profile)].find({}))
        scored = []
        for c in candidates:
            if base_profile and c.get("_id") == base_profile.get("_id"):
                continue
            skills = set(c.get("skills", []))
            interests = set(c.get("interests", []))
            shared_interests = len(base_interests & interests)
            complement_skills = len((skills - base_skills))
            shared_skills = len(base_skills & skills)
            score = 2 * shared_interests + shared_skills + 0.5 * complement_skills
            scored.append((score, c))
        scored.sort(key=lambda x: x[0], reverse=True)
        top = [serialize_doc(c) | {"match_score": s} for s, c in scored[: payload.limit]]
        return {"results": top}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------- Existing Test Endpoint ----------

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": [],
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, "name") else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:  # noqa
                response["database"] = f"⚠️  Connected but Error"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
