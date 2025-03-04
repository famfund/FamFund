# app/routes/community.py

from fastapi import APIRouter
from typing import List

# Define router object
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

@router.get("/test")
def test_community():
    return {"message": "Community route works!"}
