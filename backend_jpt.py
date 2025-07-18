from fastapi import FastAPI, Form, HTTPException
from pydantic import BaseModel, constr
from typing import Optional, List
from datetime import datetime, timedelta

app = FastAPI()

# In-memory database simulations
users = {}
investments = []

# Developer number (simulated)
DEVELOPER_PHONE = "0737734533"

# Constants
MIN_INVESTMENT = 500
MAX_INVESTMENT = 300_000
DAILY_INTEREST = 0.10
SUNDAY_BONUS = 0.05
WITHDRAWAL_FEE = 0.25

class User(BaseModel):
    username: str
    password: str
    approved: bool = False
    locked: bool = False
    failed_attempts: int = 0

class Investment(BaseModel):
    username: str
    amount: int
    receipt_number: constr(min_length=5)
    approved: bool = False
    created_at: datetime = datetime.now()
    withdrawn: bool = False

@app.post("/register/")
def register(username: str = Form(...), password: str = Form(...)):
    if username in users:
        raise HTTPException(status_code=400, detail="Username already exists.")
    users[username] = User(username=username, password=password)
    print(f"SMS to developer ({DEVELOPER_PHONE}): New user registered: {username}")
    return {"message": "Registration successful. Awaiting admin approval."}

@app.post("/login/")
def login(username: str = Form(...), password: str = Form(...)):
    user = users.get(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    if user.locked:
        raise HTTPException(status_code=403, detail="Account locked due to failed attempts.")
    if not user.approved:
        raise HTTPException(status_code=403, detail="Account not approved.")
    if user.password != password:
        user.failed_attempts += 1
        if user.failed_attempts >= 3:
            user.locked = True
        raise HTTPException(status_code=401, detail="Incorrect password.")
    user.failed_attempts = 0
    return {"message": "Login successful."}

@app.post("/invest/")
def invest(username: str = Form(...), amount: int = Form(...), receipt_number: str = Form(...)):
    user = users.get(username)
    if not user or not user.approved:
        raise HTTPException(status_code=403, detail="User not approved.")
    if amount < MIN_INVESTMENT or amount > MAX_INVESTMENT:
        raise HTTPException(status_code=400, detail="Invalid investment amount.")
    inv = Investment(username=username, amount=amount, receipt_number=receipt_number)
    investments.append(inv)
    return {"message": "Investment submitted. Awaiting admin approval."}

@app.post("/approve_user/")
def approve_user(username: str = Form(...)):
    user = users.get(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    user.approved = True
    return {"message": f"{username} approved."}

@app.post("/approve_investment/")
def approve_investment(receipt_number: str = Form(...)):
    for inv in investments:
        if inv.receipt_number == receipt_number:
            inv.approved = True
            return {"message": "Investment approved."}
    raise HTTPException(status_code=404, detail="Investment not found.")

@app.get("/investments/")
def get_all_investments():
    return investments

@app.post("/withdraw/")
def withdraw(username: str = Form(...)):
    today = datetime.now()
    if today.weekday() != 0:  # Monday is 0
        raise HTTPException(status_code=403, detail="Withdrawals allowed only on Mondays.")
    
    total_payout = 0
    for inv in investments:
        if inv.username == username and inv.approved and not inv.withdrawn:
            days = (today - inv.created_at).days
            interest = inv.amount * DAILY_INTEREST * days
            if today.weekday() == 6:  # Sunday
                interest += inv.amount * SUNDAY_BONUS
            payout = inv.amount + interest
            payout -= payout * WITHDRAWAL_FEE
            total_payout += payout
            inv.withdrawn = True

    if total_payout == 0:
        raise HTTPException(status_code=400, detail="No approved investments to withdraw.")
    
    print(f"SMS to developer ({DEVELOPER_PHONE}): {username} requested withdrawal.")
    return {"message": f"Withdrawal successful. Amount sent: KSh {int(total_payout)}"}
