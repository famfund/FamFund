from fastapi import APIRouter, HTTPException
import app.firebase as fb  # Import Firebase module

router = APIRouter()

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
