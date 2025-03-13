from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import app.firebase as fb  

router = APIRouter()

class LoanRequest(BaseModel):
    community_id: str  
    amount: float
    purpose: Optional[str] = None

class LoanVoteRequest(BaseModel):
    vote_type: str  

def get_current_user_id():
    """
    In real code, you'd decode a token or reference
    your existing auth logic. For now, we just return
    a fake user ID.
    """
    return "fakeUserId"

@router.post("/", status_code=201)
def create_loan(loan_data: LoanRequest, user_id: str = Depends(get_current_user_id)):
    """
    Submit a loan request to a particular community.
    Only members of that community can request a loan.
    """
    db = fb.db  # Firestore client

    community_ref = db.collection("communities").document(loan_data.community_id)
    community_doc = community_ref.get()
    if not community_doc.exists:
        raise HTTPException(status_code=404, detail="Community not found.")

    community_data = community_doc.to_dict()
    members = community_data.get("members", [])

    if user_id not in members:
        raise HTTPException(status_code=403, detail="User is not a member of that community.")


    loans_collection = db.collection("loans")
    new_loan_ref = loans_collection.document() 
    new_loan_data = {
        "community_id": loan_data.community_id,
        "user_id": user_id,
        "amount": loan_data.amount,
        "purpose": loan_data.purpose,
        "status": "PENDING",
        "created_at": datetime.utcnow(),

        "votes": []
    }
    new_loan_ref.set(new_loan_data)

    return {
        "message": "Loan request submitted successfully.",
        "loan_id": new_loan_ref.id,
        "status": "PENDING"
    }

@router.post("/{loan_id}/vote", status_code=200)
def vote_on_loan(loan_id: str, vote_data: LoanVoteRequest, user_id: str = Depends(get_current_user_id)):
    """
    Cast a vote on an existing loan. Only members
    of that community can vote.
    """
    db = fb.db
    loan_ref = db.collection("loans").document(loan_id)
    loan_doc = loan_ref.get()
    if not loan_doc.exists:
        raise HTTPException(status_code=404, detail="Loan not found.")

    loan_data = loan_doc.to_dict()

    community_ref = db.collection("communities").document(loan_data["community_id"])
    community_doc = community_ref.get()
    if not community_doc.exists:
        raise HTTPException(status_code=404, detail="Community not found.")
    
    community_data = community_doc.to_dict()
    members = community_data.get("members", [])

    if user_id not in members:
        raise HTTPException(
            status_code=403,
            detail="User is not a member of this community."
        )

    votes = loan_data.get("votes", [])

    existing_vote = next((v for v in votes if v["user_id"] == user_id), None)
    if existing_vote:
        existing_vote["vote_type"] = vote_data.vote_type
    else:
        votes.append({"user_id": user_id, "vote_type": vote_data.vote_type})

    updated_data = {
        "votes": votes,
        "updated_at": datetime.utcnow()
    }
    loan_ref.update(updated_data)

    return {"message": f"Vote '{vote_data.vote_type}' recorded for loan {loan_id}."}
