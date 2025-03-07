from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
import app.firebase as fb
from firebase_admin import auth
from typing import List, Dict

router = APIRouter()

# Store active WebSocket connections per community
active_connections: Dict[str, List[WebSocket]] = {}

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
        community_data = {
            "community_id": community_ref.id,
            "name": request.name,
            "description": request.description,
            "created_by": user_id,
            "members": [],
            "max_members": 100
        }
        community_ref.set(community_data)

        return {"message": "Community created successfully", "community_id": community_ref.id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{community_id}/join")
async def join_community(community_id: str, authorization: str):
    """Allows users to join a community, enforcing the 100-member limit and sending live updates."""
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

        if len(community_data.get("members", [])) >= community_data.get("max_members", 100):
            raise HTTPException(status_code=403, detail="Community is full (100 members max).")

        # Update community with new member
        updated_members = community_data["members"] + [user_id]
        community_ref.update({"members": updated_members})

        # Broadcast update to WebSocket clients
        await broadcast_update(community_id, {"message": f"New member joined: {user_id}", "members": updated_members})

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

        if not community_doc.exists():
            raise HTTPException(status_code=404, detail="Community not found.")

        community_data = community_doc.to_dict()
        return community_data.get("members", [])

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{community_id}/archive")
async def archive_community(community_id: str):
    """
    Archives a community if it's inactive.
    """
    if fb.db is None:
        fb.initialize_firebase()

    try:
        community_ref = fb.db.collection("communities").document(community_id)
        community_doc = community_ref.get()

        if not community_doc.exists():
            raise HTTPException(status_code=404, detail="Community not found.")

        community_ref.update({"is_archived": True})

        # Broadcast archive update
        await broadcast_update(community_id, {"message": f"Community {community_id} has been archived."})

        return {"message": f"Community {community_id} archived."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

#WebSocket Endpoint for Live Updates
@router.websocket("/{community_id}/updates")
async def websocket_endpoint(websocket: WebSocket, community_id: str):
    """
    WebSocket connection for real-time community updates.
    """
    await websocket.accept()
    
    if community_id not in active_connections:
        active_connections[community_id] = []
    active_connections[community_id].append(websocket)

    try:
        while True:
            # Keep connection open
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_connections[community_id].remove(websocket)

async def broadcast_update(community_id: str, data: dict):
    """
    Sends real-time updates to all connected WebSocket clients.
    """
    if community_id in active_connections:
        for connection in active_connections[community_id]:
            await connection.send_json(data)
