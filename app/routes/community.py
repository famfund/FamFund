from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import app.firebase as fb  # Import Firebase module
from firebase_admin import auth
from typing import List

router = APIRouter()

# Mock data: Dictionary where keys are community IDs, and values are lists of members
communities = {
    1: ["Alice", "Bob", "Charlie"],
    2: ["David", "Eve", "Frank"],
    3: ["Grace", "Hank", "Ivy"]
}

@router.get("/api/community/members/{community_id}", response_model=List[str])
def get_community_members(community_id: int):
    """
    Retrieve all members of a given community by community_id.
    If the community does not exist, return an empty list.
    """
    return communities.get(community_id, [])

class Community(BaseModel):
    community_name: str
    description: str
    platform_id: str

def verify_token(token: str):
    '''
    Verifies authentication token, retrieves user details.
    '''
    try: 
        verified_token = auth.verify_id_token(token)
        user_id = verified_token["uid"]
        return user_id
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    
def verify_user(user_id: str):
    """
    Checks if given user is an investment platform.
    """
    if fb.db is None:
        fb.initialize_firebase()

    user_doc = fb.db.collection("users").document(user_id).get()
    if not user_doc.exists:
        raise HTTPException(status_code=403, detail="User not found.")

    user_data = user_doc.to_dict()
    if user_data.get("role") != "investment_platform":
        raise HTTPException(status_code=403, detail="Only investment platforms can approve communitites.")
    
    return user_data

@router.post("/approve")
def approve_community(request: Community, authorization: str):
    # checks authorization to ensure only investment platforms can approve
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization code required.")
    
    user_id = verify_token(authorization)
    verify_user(user_id)

    if fb.db is None:
        fb.initialize_firebase()

    #create new community
    try:
        community_ref = fb.db.collection("communites").document()
        community_ref.set({
            "community_id": community_ref.id,
            "community_name": request.community_name,
            "description": request.description,
            "platform_id": request.platform_id,
            "approved_by": user_id,
            "status": "approved",
            "members": []
        })

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
            raise HTTPException(status_code=404, detail="Community not found")

        community_ref.update({"is_archived": True})

        return {"message": f"Community {community_id} archived."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
