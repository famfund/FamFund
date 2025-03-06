from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import app.firebase as fb
from firebase_admin import auth
from typing import List

router = APIRouter()

# 🔹 Dummy community members data for testing (Can be removed later)
communities = {
    "1": ["Alice", "Bob", "Charlie"],
    "2": ["David", "Eve", "Frank"],
    "3": ["Grace", "Hank", "Ivy"]
}

@router.get("/{community_id}/members", response_model=List[str])
def get_community_members(community_id: str):
    """
    Retrieve all members of a given community.
    If the community does not exist, return an empty list.
    """
    return communities.get(community_id, [])

# 🔹 Data Model for community approval
class Community(BaseModel):
    community_name: str
    description: str
    platform_id: str

def verify_token(token: str):
    """Verifies authentication token and retrieves user ID."""
    try: 
        decoded_token = auth.verify_id_token(token)
        return decoded_token.get("uid")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid authentication token")

def verify_user(user_id: str):
    """Checks if the user is an investment platform."""
    if fb.db is None:
        fb.initialize_firebase()

    user_doc = fb.db.collection("users").document(user_id).get()
    if not user_doc.exists:
        raise HTTPException(status_code=403, detail="User not found.")

    user_data = user_doc.to_dict()
    if user_data.get("role") != "investment_platform":
        raise HTTPException(status_code=403, detail="Only investment platforms can approve communities.")

    return user_data

@router.post("/approve")
def approve_community(request: Community, authorization: str):
    """
    Approves a new community (only investment platforms can approve).
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization token required.")

    user_id = verify_token(authorization)
    verify_user(user_id)

    if fb.db is None:
        fb.initialize_firebase()

    try:
        # Create new community document
        community_ref = fb.db.collection("communities").document()
        community_data = {
            "community_id": community_ref.id,
            "community_name": request.community_name,
            "description": request.description,
            "platform_id": request.platform_id,
            "approved_by": user_id,
            "status": "approved",
            "members": []
        }
        community_ref.set(community_data)

        return {"message": "Community approved successfully", "community_id": community_ref.id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{community_id}/archive")
def archive_community(community_id: str):
    """
    Archives a community if it's inactive.
    """
    if fb.db is None:
        fb.initialize_firebase()

    try:
        community_ref = fb.db.collection("communities").document(community_id)
        community_doc = community_ref.get()

        if not community_doc.exists:
            raise HTTPException(status_code=404, detail="Community not found.")

        community_ref.update({"is_archived": True})

        return {"message": f"Community {community_id} archived."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
