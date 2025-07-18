from fastapi import FastAPI, HTTPException, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from datetime import datetime, timedelta
import uvicorn

app = FastAPI()

users_db = {}
investments_db = {}
withdrawal_requests = []

ADMIN_PASSWORD = "admin123"
DEVELOPER_NUMBER = "0737734533"

class User(BaseModel):
    username: str
    password: str
    phone: str

class Investment(BaseModel):
    username: str
    amount: float
    receipt_number: str

@app.post("/register")
def register(user: User):
    if user.username in users_db:
        raise HTTPException(status_code=400, detail="Username already exists")
    users_db[user.username] = {
        "password": user.password,
        "phone": user.phone,
        "approved": False,
        "investments": [],
        "balance": 0,
    }
    send_sms(f"New user registered: {user.username}", DEVELOPER_NUMBER)
    return {"message": "Registration successful. Await admin approval."}

@app.post("/login")
def login(username: str = Form(...), password: str = Form(...)):
    user = users_db.get(username)
    if not user or user["password"] != password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user["approved"]:
        raise HTTPException(status_code=403, detail="Account not approved yet")
    return {"message": "Login successful"}

@app.post("/invest")
def invest(investment: Investment):
    if investment.username not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    if not users_db[investment.username]["approved"]:
        raise HTTPException(status_code=403, detail="Account not approved yet")
    if investment.amount < 500 or investment.amount > 300000:
        raise HTTPException(status_code=400, detail="Amount must be between 500 and 300,000")
    
    record = {
        "amount": investment.amount,
        "receipt": investment.receipt_number,
        "date": datetime.now(),
        "approved": False
    }
    users_db[investment.username]["investments"].append(record)
    send_sms(f"Investment submitted by {investment.username} - Ksh {investment.amount}", DEVELOPER_NUMBER)
    return {"message": "Investment submitted. Awaiting admin approval."}

@app.post("/admin/approve_user")
def approve_user(username: str, password: str = Form(...)):
    if password != ADMIN_PASSWORD:
        raise HTTPException(status_code=403, detail="Unauthorized")
    if username in users_db:
        users_db[username]["approved"] = True
        return {"message": f"{username} approved"}
    raise HTTPException(status_code=404, detail="User not found")

@app.post("/admin/approve_investment")
def approve_investment(username: str, password: str = Form(...)):
    if password != ADMIN_PASSWORD:
        raise HTTPException(status_code=403, detail="Unauthorized")
    user = users_db.get(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    for investment in user["investments"]:
        if not investment["approved"]:
            investment["approved"] = True
            investment["start_date"] = datetime.now()
            send_sms(f"Investment approved for {username}", DEVELOPER_NUMBER)
            return {"message": f"Approved one investment for {username}"}
    return {"message": "No pending investments"}

@app.get("/admin/view_users")
def view_users(password: str):
    if password != ADMIN_PASSWORD:
        raise HTTPException(status_code=403, detail="Unauthorized")
    return users_db

@app.post("/earnings/daily")
def apply_daily_earnings(password: str):
    if password != ADMIN_PASSWORD:
        raise HTTPException(status_code=403, detail="Unauthorized")
    today = datetime.now()
    for user in users_db.values():
        for inv in user["investments"]:
            if inv.get("approved") and "start_date" in inv:
                days = (today - inv["start_date"]).days
                earnings = days * 0.10 * inv["amount"]
                if today.weekday() == 6:  # Sunday bonus
                    earnings += 0.05 * inv["amount"]
                user["balance"] = user.get("balance", 0) + earnings
    return {"message": "Daily earnings applied"}

@app.post("/withdraw")
def withdraw(username: str, password: str = Form(...)):
    today = datetime.now()
    if today.weekday() != 0:
        raise HTTPException(status_code=403, detail="Withdrawals only allowed on Mondays")
    user = users_db.get(username)
    if not user or user["password"] != password:
        raise HTTPException(status_code=403, detail="Unauthorized")
    amount = user.get("balance", 0)
    if amount <= 0:
        raise HTTPException(status_code=400, detail="No balance to withdraw")
    final_amount = amount * 0.75  # 25% deduction
    withdrawal_requests.append({
        "username": username,
        "amount": final_amount,
        "timestamp": today
    })
    user["balance"] = 0
    send_sms(f"Withdrawal requested: {username} - Ksh {final_amount}", DEVELOPER_NUMBER)
    return {"message": f"Ksh {final_amount} withdrawal requested. Await processing."}

def send_sms(message: str, to_number: str):
    print(f"SMS to {to_number}: {message}")

@app.get("/")
def root():
    return {"message": "Welcome to Jipate Bonus API"}

if __name__ == "__main__":
    uvicorn.run("jipate:app", host="0.0.0.0", port=8000, reload=True)
