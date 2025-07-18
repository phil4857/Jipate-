from fastapi import FastAPI, Form, HTTPException
from pydantic import BaseModel
from datetime import datetime
from typing import Dict
import random

app = FastAPI()

# In-memory storage
users: Dict[str, dict] = {}
investments: Dict[str, dict] = {}

# Constants
MIN_INVESTMENT = 500
MAX_INVESTMENT = 300000
ADMIN_PASSWORD = "admin123"
DEVELOPER_PHONE = "0737734533"

# Models
class User(BaseModel):
    username: str
    phone: str
    password: str
    approved: bool = False

class Investment(BaseModel):
    username: str
    amount: float
    receipt_number: str
    approved: bool = False
    timestamp: datetime = datetime.now()

@app.post("/register/")
def register_user(username: str = Form(...), phone: str = Form(...), password: str = Form(...)):
    if username in users:
        raise HTTPException(status_code=400, detail="User already exists.")
    users[username] = User(username=username, phone=phone, password=password)
    print(f"SMS to developer ({DEVELOPER_PHONE}): New user {username} registered.")
    return {"message": "User registered. Awaiting admin approval."}

@app.post("/login/")
def login_user(username: str = Form(...), password: str = Form(...)):
    user = users.get(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    if user.password != password:
        raise HTTPException(status_code=401, detail="Incorrect password.")
    if not user.approved:
        raise HTTPException(status_code=403, detail="User not approved.")
    return {"message": "Login successful."}

@app.post("/admin/approve_user/")
def approve_user(username: str = Form(...), admin_password: str = Form(...)):
    if admin_password != ADMIN_PASSWORD:
        raise HTTPException(status_code=403, detail="Invalid admin password.")
    user = users.get(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    user.approved = True
    return {"message": f"User {username} approved."}

@app.post("/invest/")
def make_investment(username: str = Form(...), amount: float = Form(...), receipt_number: str = Form(...)):
    if username not in users or not users[username].approved:
        raise HTTPException(status_code=403, detail="User not approved or not found.")
    if amount < MIN_INVESTMENT or amount > MAX_INVESTMENT:
        raise HTTPException(status_code=400, detail="Amount out of range.")
    inv_id = f"{username}_{random.randint(1000, 9999)}"
    investments[inv_id] = Investment(username=username, amount=amount, receipt_number=receipt_number)
    return {"message": "Investment submitted. Awaiting admin approval."}

@app.post("/admin/approve_investment/")
def approve_investment(investment_id: str = Form(...), admin_password: str = Form(...)):
    if admin_password != ADMIN_PASSWORD:
        raise HTTPException(status_code=403, detail="Invalid admin password.")
    investment = investments.get(investment_id)
    if not investment:
        raise HTTPException(status_code=404, detail="Investment not found.")
    investment.approved = True
    return {"message": f"Investment {investment_id} approved."}

@app.get("/withdraw/")
def withdraw(username: str):
    if username not in users or not users[username].approved:
        raise HTTPException(status_code=403, detail="User not approved or not found.")
    
    approved_investments = [i for i in investments.values() if i.username == username and i.approved]
    if not approved_investments:
        raise HTTPException(status_code=400, detail="No approved investments.")

    total_amount = sum(i.amount for i in approved_investments)
    today = datetime.today()
    is_sunday = today.weekday() == 6
    if today.weekday() != 0:  # Withdrawals only on Monday
        raise HTTPException(status_code=403, detail="Withdrawals only allowed on Mondays.")
    
    daily_interest = total_amount * 0.10
    sunday_bonus = total_amount * 0.05 if is_sunday else 0
    gross = total_amount + daily_interest + sunday_bonus
    deduction = gross * 0.25
    net = gross - deduction

    print(f"SMS to developer ({DEVELOPER_PHONE}): {username} requested withdrawal.")

    return {
        "total_invested": total_amount,
        "daily_interest": daily_interest,
        "sunday_bonus": sunday_bonus,
        "gross_amount": gross,
        "deduction": deduction,
        "net_withdrawal": net
    }

@app.get("/admin/view_users/")
def view_all_users(admin_password: str):
    if admin_password != ADMIN_PASSWORD:
        raise HTTPException(status_code=403, detail="Invalid admin password.")
    return users

@app.get("/admin/view_investments/")
def view_all_investments(admin_password: str):
    if admin_password != ADMIN_PASSWORD:
        raise HTTPException(status_code=403, detail="Invalid admin password.")
    return investments
