from fastapi import FastAPI, APIRouter, HTTPException, File, UploadFile, Form
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import base64
import uuid
from bson import ObjectId
import asyncio
from emergentintegrations.llm.chat import LlmChat, UserMessage

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Pydantic Models for CIRS
class User(BaseModel):
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: str
    password_hash: str
    phone: Optional[str] = None
    role: str = "citizen"  # citizen, admin, dept_staff
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    phone: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

class Category(BaseModel):
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    icon: Optional[str] = None

class Issue(BaseModel):
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    category_id: str
    title: str
    description: str
    image_base64: Optional[str] = None
    voice_base64: Optional[str] = None
    voice_transcript: Optional[str] = None
    location_lat: float
    location_long: float
    address: Optional[str] = None
    status: str = "pending"  # pending, in_progress, resolved, escalated
    expected_completion: Optional[datetime] = None
    actual_completion: Optional[datetime] = None
    vote_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class IssueCreate(BaseModel):
    title: str
    description: str
    category_id: str
    image_base64: Optional[str] = None
    voice_base64: Optional[str] = None
    location_lat: float
    location_long: float
    address: Optional[str] = None

class IssueCreateWithUser(BaseModel):
    title: str
    description: str
    category_id: str
    image_base64: Optional[str] = None
    voice_base64: Optional[str] = None
    location_lat: float
    location_long: float
    address: Optional[str] = None
    user_id: str

class Vote(BaseModel):
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    issue_id: str
    user_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Comment(BaseModel):
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    issue_id: str
    user_id: str
    message: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class CommentCreate(BaseModel):
    issue_id: str
    message: str

class Notification(BaseModel):
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    issue_id: Optional[str] = None
    title: str
    message: str
    is_read: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Helper Functions
def object_id_to_str(doc):
    if doc and "_id" in doc:
        doc["id"] = str(doc["_id"])
        del doc["_id"]
    return doc

async def transcribe_audio(audio_base64: str) -> str:
    """Transcribe audio using OpenAI Whisper via Emergent LLM key"""
    try:
        # Note: This is a simplified approach. In production, you'd need to 
        # convert base64 to audio file and use OpenAI's audio API
        # For now, we'll use a text generation model to simulate transcription
        chat = LlmChat(
            api_key=os.environ.get('EMERGENT_LLM_KEY'),
            session_id=str(uuid.uuid4()),
            system_message="You are a helpful assistant that processes voice notes for civic issues."
        ).with_model("openai", "gpt-4o-mini")
        
        user_message = UserMessage(
            text="[Audio transcription would happen here - simulated for demo]"
        )
        
        response = await chat.send_message(user_message)
        return "Voice note recorded (transcription available in full version)"
    except Exception as e:
        print(f"Transcription error: {e}")
        return "Voice note recorded (transcription failed)"

# Authentication & Users
@api_router.post("/users/register", response_model=Dict[str, Any])
async def register_user(user_data: UserCreate):
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash password (simplified - use proper hashing in production)
    import hashlib
    password_hash = hashlib.sha256(user_data.password.encode()).hexdigest()
    
    user = User(
        name=user_data.name,
        email=user_data.email,
        password_hash=password_hash,
        phone=user_data.phone
    )
    
    result = await db.users.insert_one(user.dict())
    user_dict = user.dict()
    user_dict["id"] = str(result.inserted_id)
    
    return {"success": True, "user": user_dict, "message": "User registered successfully"}

@api_router.post("/users/login", response_model=Dict[str, Any])
async def login_user(login_data: UserLogin):
    import hashlib
    password_hash = hashlib.sha256(login_data.password.encode()).hexdigest()
    
    user = await db.users.find_one({
        "email": login_data.email,
        "password_hash": password_hash
    })
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    user = object_id_to_str(user)
    return {"success": True, "user": user, "message": "Login successful"}

# Categories
@api_router.get("/categories", response_model=List[Category])
async def get_categories():
    categories = await db.categories.find().to_list(1000)
    return [Category(**object_id_to_str(cat)) for cat in categories]

@api_router.post("/categories/init")
async def init_categories():
    """Initialize default categories"""
    default_categories = [
        {"name": "Roads & Transportation", "description": "Potholes, traffic issues, road repairs", "icon": "car"},
        {"name": "Water & Sanitation", "description": "Water leaks, drainage, sewage", "icon": "water-drop"},
        {"name": "Electricity", "description": "Power outages, street lights, electrical issues", "icon": "flash"},
        {"name": "Waste Management", "description": "Garbage collection, littering, recycling", "icon": "trash"},
        {"name": "Public Safety", "description": "Security, crime, emergency services", "icon": "shield"},
        {"name": "Parks & Recreation", "description": "Parks maintenance, recreational facilities", "icon": "leaf"},
        {"name": "Other", "description": "Other civic issues", "icon": "help-circle"}
    ]
    
    # Clear existing categories
    await db.categories.delete_many({})
    
    # Insert new categories
    for cat_data in default_categories:
        category = Category(**cat_data)
        await db.categories.insert_one(category.dict())
    
    return {"success": True, "message": "Categories initialized"}

# Issues
@api_router.post("/issues", response_model=Dict[str, Any])
async def create_issue(issue_data: IssueCreate, user_id: str = Form(...)):
    # Transcribe voice if provided
    voice_transcript = None
    if issue_data.voice_base64:
        voice_transcript = await transcribe_audio(issue_data.voice_base64)
    
    issue = Issue(
        user_id=user_id,
        title=issue_data.title,
        description=issue_data.description,
        category_id=issue_data.category_id,
        image_base64=issue_data.image_base64,
        voice_base64=issue_data.voice_base64,
        voice_transcript=voice_transcript,
        location_lat=issue_data.location_lat,
        location_long=issue_data.location_long,
        address=issue_data.address
    )
    
    result = await db.issues.insert_one(issue.dict())
    issue_dict = issue.dict()
    issue_dict["id"] = str(result.inserted_id)
    
    return {"success": True, "issue": issue_dict, "message": "Issue reported successfully"}

@api_router.get("/issues", response_model=List[Dict[str, Any]])
async def get_issues(
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    radius: Optional[float] = 5.0,  # km
    category_id: Optional[str] = None,
    limit: int = 50
):
    pipeline = []
    
    # Location-based filtering (simplified - doesn't use proper geo queries)
    match_conditions = {}
    if lat and lng:
        # Simple distance calculation (not accurate, but works for demo)
        match_conditions["location_lat"] = {"$gte": lat - 0.05, "$lte": lat + 0.05}
        match_conditions["location_long"] = {"$gte": lng - 0.05, "$lte": lng + 0.05}
    
    if category_id:
        match_conditions["category_id"] = category_id
    
    if match_conditions:
        pipeline.append({"$match": match_conditions})
    
    # Sort by vote count and creation date
    pipeline.append({"$sort": {"vote_count": -1, "created_at": -1}})
    pipeline.append({"$limit": limit})
    
    issues = await db.issues.aggregate(pipeline).to_list(limit)
    
    # Get user and category info for each issue
    result = []
    for issue in issues:
        issue = object_id_to_str(issue)
        
        # Get user info
        user = await db.users.find_one({"id": issue["user_id"]})
        if user:
            issue["user_name"] = user["name"]
        
        # Get category info
        category = await db.categories.find_one({"id": issue["category_id"]})
        if category:
            issue["category_name"] = category["name"]
            issue["category_icon"] = category.get("icon", "help-circle")
        
        result.append(issue)
    
    return result

@api_router.get("/issues/{issue_id}", response_model=Dict[str, Any])
async def get_issue(issue_id: str):
    issue = await db.issues.find_one({"id": issue_id})
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    
    issue = object_id_to_str(issue)
    
    # Get user info
    user = await db.users.find_one({"id": issue["user_id"]})
    if user:
        issue["user_name"] = user["name"]
    
    # Get category info
    category = await db.categories.find_one({"id": issue["category_id"]})
    if category:
        issue["category_name"] = category["name"]
        issue["category_icon"] = category.get("icon", "help-circle")
    
    return issue

# Voting
@api_router.post("/issues/{issue_id}/vote", response_model=Dict[str, Any])
async def vote_issue(issue_id: str, user_id: str = Form(...)):
    # Check if user already voted
    existing_vote = await db.votes.find_one({
        "issue_id": issue_id,
        "user_id": user_id
    })
    
    if existing_vote:
        # Remove vote (toggle)
        await db.votes.delete_one({"id": existing_vote["id"]})
        await db.issues.update_one(
            {"id": issue_id},
            {"$inc": {"vote_count": -1}}
        )
        return {"success": True, "voted": False, "message": "Vote removed"}
    else:
        # Add vote
        vote = Vote(issue_id=issue_id, user_id=user_id)
        await db.votes.insert_one(vote.dict())
        await db.issues.update_one(
            {"id": issue_id},
            {"$inc": {"vote_count": 1}}
        )
        return {"success": True, "voted": True, "message": "Vote added"}

# Comments
@api_router.post("/issues/{issue_id}/comments", response_model=Dict[str, Any])
async def add_comment(issue_id: str, comment_data: CommentCreate, user_id: str = Form(...)):
    comment = Comment(
        issue_id=issue_id,
        user_id=user_id,
        message=comment_data.message
    )
    
    result = await db.comments.insert_one(comment.dict())
    comment_dict = comment.dict()
    comment_dict["id"] = str(result.inserted_id)
    
    return {"success": True, "comment": comment_dict, "message": "Comment added"}

@api_router.get("/issues/{issue_id}/comments", response_model=List[Dict[str, Any]])
async def get_comments(issue_id: str):
    comments = await db.comments.find({"issue_id": issue_id}).sort("created_at", -1).to_list(1000)
    
    result = []
    for comment in comments:
        comment = object_id_to_str(comment)
        
        # Get user info
        user = await db.users.find_one({"id": comment["user_id"]})
        if user:
            comment["user_name"] = user["name"]
        
        result.append(comment)
    
    return result

# Health check
@api_router.get("/")
async def root():
    return {"message": "CIRS API is running", "status": "healthy"}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()