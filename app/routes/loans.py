from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import app.firebase as fb  

router = APIRouter()

# Data Models

class LoanRequest(BaseModel):
    community_id: str  
    amount: float
    purpose: Optional[str] = None

class LoanVoteRequest(BaseModel):
    vote_type: str  # Example: 'approve' or 'reject'

# Helper functions

def get_current_user_id():
    """
    Mock user ID retrieval for development purposes.
    Replace this with real authentication logic.
    """
    return "mockUserId"

# end points

@router.post("/", status_code=201)
def submit_loan_request(loan: LoanRequest, user_id: str = Depends(get_current_user_id)):
    """
    Submit a loan request to a community.
    Only members of the community can submit a request.
    """
    db = fb.db  
    community = db.collection("communities").document(loan.community_id).get()

    if not community.exists:
        raise HTTPException(status_code=404, detail="Community not found.")

    if user_id not in community.to_dict().get("members", []):
        raise HTTPException(status_code=403, detail="User is not a member of this community.")

    loan_ref = db.collection("loans").document()
    loan_ref.set({
        "loan_id": loan_ref.id,
        "community_id": loan.community_id,
        "user_id": user_id,
        "amount": loan.amount,
        "purpose": loan.purpose,
        "status": "PENDING",
        "created_at": datetime.utcnow(),
        "votes": []
    })

    return {"message": "Loan request submitted successfully.", "loan_id": loan_ref.id, "status": "PENDING"}


@router.post("/{loan_id}/vote", status_code=200)
def cast_vote_on_loan(loan_id: str, vote: LoanVoteRequest, user_id: str = Depends(get_current_user_id)):
    """
    Cast a vote on a loan request. Only community members can vote.
    """
    db = fb.db
    loan = db.collection("loans").document(loan_id).get()

    if not loan.exists:
        raise HTTPException(status_code=404, detail="Loan not found.")

    loan_data = loan.to_dict()
    community = db.collection("communities").document(loan_data["community_id"]).get()

    if not community.exists or user_id not in community.to_dict().get("members", []):
        raise HTTPException(status_code=403, detail="User is not a member of this community.")

    votes = loan_data.get("votes", [])
    existing_vote = next((v for v in votes if v["user_id"] == user_id), None)

    if existing_vote:
        existing_vote["vote_type"] = vote.vote_type
    else:
        votes.append({"user_id": user_id, "vote_type": vote.vote_type})

    db.collection("loans").document(loan_id).update({
        "votes": votes,
        "updated_at": datetime.utcnow()
    })

    return {"message": f"Vote '{vote.vote_type}' recorded for loan {loan_id}."}


@router.get("/{loan_id}", status_code=200)
def get_loan_details(loan_id: str):
    """
    Retrieve the details of a specific loan request by ID.
    """
    db = fb.db
    loan = db.collection("loans").document(loan_id).get()

    if not loan.exists:
        raise HTTPException(status_code=404, detail="Loan not found.")

    return loan.to_dict()


@router.get("/user/{user_id}", response_model=List[dict])
def get_loans_by_user(user_id: str):
    """
    Retrieve all loan requests made by a specific user.
    """
    db = fb.db
    loan_docs = db.collection("loans").where("user_id", "==", user_id).stream()

    loans = [
        {
            "loan_id": loan.id,
            **loan.to_dict()
        }
        for loan in loan_docs
    ]

    if not loans:
        raise HTTPException(status_code=404, detail="No loan requests found for this user.")

    return loans
