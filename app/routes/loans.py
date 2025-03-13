from fastapi import APIRouter, HTTPException
import app.firebase as fb

router = APIRouter()

@router.get("/{loan_id}")
def get_loan_details(loan_id: str):
   """
   Retrieves the status and details of a specific loan.
   """
   if fb.db is None:
       fb.initialize_firebase()

   try:
       loan_ref = fb.db.collection("loans").document(loan_id)
       loan_doc = loan_ref.get()

       if not loan_doc.exists:
           raise HTTPException(status_code=404, detail="Loan not found.")

       return loan_doc.to_dict()

   except Exception as e:
       raise HTTPException(status_code=500, detail=str(e))
