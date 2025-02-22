from fastapi import FastAPI
from app.routes import auth, community, loans, funds, repayments, admin, notifications, chat, search, transactions

app = FastAPI()

# Register routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(community.router, prefix="/api/community", tags=["Community"])
app.include_router(loans.router, prefix="/api/community-loans", tags=["Community Loans"])
app.include_router(funds.router, prefix="/api/funds", tags=["Funds"])
app.include_router(repayments.router, prefix="/api/repayment", tags=["Repayment"])
app.include_router(admin.router, prefix="/api/community/moderator", tags=["Admin"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["Notifications"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(search.router, prefix="/api/search", tags=["Search"])
app.include_router(transactions.router, prefix="/api/transactions", tags=["Transactions"])

@app.get("/")
def root():
    return {"message": "FamFund API is running!"}