from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import app.firebase as fb
from firebase_admin import auth
from typing import List

router = APIRouter()

class Community(BaseModel):
    name: str
    description: str = ""

def verify_token(token: str):
    """Verifies Firebase authentication token and retrieves user ID."""
    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token.get("uid")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid authentication token")

@router.post("/")
def create_community(request: Community, authorization: str):
    """Creates a new community (only for authenticated users)."""
    user_id = verify_token(authorization)

    if fb.db is None:
        fb.initialize_firebase()

    try:
        community_ref = fb.db.collection("communities").document()
        community_ref.set({
            "community_id": community_ref.id,
            "name": request.name,
            "description": request.description,
            "created_by": user_id,
            "members": [user_id],  # Automatically add creator as a member
        })

        return {"message": "Community created successfully", "community_id": community_ref.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{community_id}/join")
def join_community(community_id: str, authorization: str):
    """Allows users to join a community."""
    user_id = verify_token(authorization)

    if fb.db is None:
        fb.initialize_firebase()

    try:
        community_ref = fb.db.collection("communities").document(community_id)
        community_doc = community_ref.get()

        if not community_doc.exists:
            raise HTTPException(status_code=404, detail="Community not found.")

        community_data = community_doc.to_dict()

        if user_id in community_data.get("members", []):
            raise HTTPException(status_code=400, detail="User is already a member.")

        community_ref.update({"members": community_data["members"] + [user_id]})

        return {"message": "Successfully joined the community."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{community_id}/members", response_model=List[str])
def list_community_members(community_id: str):
    """Returns a list of community members."""
    if fb.db is None:
        fb.initialize_firebase()

    try:
        community_ref = fb.db.collection("communities").document(community_id)
        community_doc = community_ref.get()

        if not community_doc.exists:
            raise HTTPException(status_code=404, detail="Community not found.")

        community_data = community_doc.to_dict()
        return community_data.get("members", [])

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
