# app/routes/community.py

from fastapi import APIRouter

# Define router object
router = APIRouter()

@router.get("/test")
def test_community():
    return {"message": "Community route works!"}
