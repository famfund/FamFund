from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import app.firebase as fb  # Import the firebase module, not just db

router = APIRouter()

class LoginRequest(BaseModel):
    platform_id: str
    user_id: str
    token: str

@router.post("/login")
def login(request: LoginRequest):
    # Ensure that Firebase is initialized (if somehow not yet done)
    if fb.db is None:
        fb.initialize_firebase()
    try:
        user_doc = fb.db.collection("users").document(request.user_id).get()
        if not user_doc.exists:
            raise HTTPException(status_code=404, detail="User not found")
        user_data = user_doc.to_dict()
        return {
            "message": "Login successful",
            "user_id": request.user_id,
            "email": user_data.get("email"),
            "full_legal_name": user_data.get("full_legal_name"),
            "investment_history": user_data.get("investment_history", []),
            "current_investments": user_data.get("current_investments", []),
            "transaction_history": user_data.get("transaction_history", []),
            "cash_balance": user_data.get("cash_balance", 0),
            "margin_accounts": user_data.get("margin_accounts", [])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/me")
def get_logged_in_user(user_id: str):
    if fb.db is None:
        fb.initialize_firebase()
    try:
        user_doc = fb.db.collection("users").document(user_id).get()
        if not user_doc.exists:
            raise HTTPException(status_code=404, detail="User not found")
        user_data = user_doc.to_dict()
        return {
            "user_id": user_id,
            "email": user_data.get("email"),
            "full_legal_name": user_data.get("full_legal_name"),
            "investment_history": user_data.get("investment_history", []),
            "current_investments": user_data.get("current_investments", []),
            "transaction_history": user_data.get("transaction_history", []),
            "cash_balance": user_data.get("cash_balance", 0),
            "margin_accounts": user_data.get("margin_accounts", [])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/logout")
def logout():
    return {"message": "Logout successful"}
