from fastapi import FastAPI, WebSocket
from app.firebase import initialize_firebase  # Initialize Firebase here
from app.routes import auth, community, loans  # Import routers including loans

# Initialize Firebase
initialize_firebase()

# Initialize FastAPI App
app = FastAPI()

# Register Routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(community.router, prefix="/api/community", tags=["Community"])
app.include_router(loans.router, prefix="/api/community-loans", tags=["Community Loans"])

# Root Endpoint
@app.get("/")
def root():
    return {"message": "FamFund API is running with WebSocket support!"}


# WebSocket Endpoint for Real-Time Community Updates
@app.websocket("/ws/community/{community_id}")
async def community_updates(websocket: WebSocket, community_id: str):
    await websocket.accept()
    await websocket.send_text(f"Connected to community {community_id} updates!")

    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Received in community {community_id}: {data}")

    except Exception as e:
        print(f"WebSocket closed: {e}")
        await websocket.close()
