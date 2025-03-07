from fastapi import FastAPI
from app.firebase import initialize_firebase  #Initialize Firebase here
from app.routes import auth, community  #Import both auth and community routers

#Initialize Firebase
initialize_firebase()

#Initialize FastAPI App
app = FastAPI()

#Register Routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(community.router, prefix="/api/community", tags=["Community"])

#Root Endpoint
@app.get("/")
def root():
    return {"message": "FamFund API is running with WebSocket support!"}

