from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from firebase_admin import auth
import app.firebase as fb

router = APIRouter()

class LoginRequest(BaseModel):
    platform_id: str
    user_id: str
    token: str

def verify_token(token: str):
    """
    Verifies the provided Firebase authentication token.
    """
    try:
        verified_token = auth.verify_id_token(token)
        return verified_token.get("uid")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired authentication token")

@router.post("/login")
def login(request: LoginRequest):
    """
    Handles user login after verifying their token and ID.
    """
    if fb.db is None:
        fb.initialize_firebase()

    # Verify token and match user ID
    verified_user_id = verify_token(request.token)
    if verified_user_id != request.user_id:
        raise HTTPException(status_code=403, detail="Token does not match user ID.")

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
def get_logged_in_user(user_id: str, authorization: str = Header(None)):
    """
    Retrieves details for the authenticated user.
    """
    if fb.db is None:
        fb.initialize_firebase()

    # Verify the authorization token
    verified_user_id = verify_token(authorization)
    if verified_user_id != user_id:
        raise HTTPException(status_code=403, detail="Token does not match user ID.")

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
    """
    Handles user logout.
    """
    return {"message": "Logout successful"}
