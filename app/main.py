from fastapi import FastAPI
from app.firebase import initialize_firebase  # Import the initialization function
from app.routes import auth  # Import the auth router

# Initialize Firebase (this will set up the global Firestore client)
initialize_firebase()

app = FastAPI()

# Register the auth router
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])

# Root endpoint
@app.get("/")
def root():
    return {"message": "FamFund API is running!"}
