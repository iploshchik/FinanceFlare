from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from typing import List, Optional
from fastapi import UploadFile, File
import pandas as pd
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from app.database import get_db
from app.models import Transaction, TransactionCreate, TransactionResponse, CategoryRule
from app.services.categorization import categorize_transaction
from app.utils.auth import SECRET_KEY, ALGORITHM

router = APIRouter()

# Authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_current_user(token: str = Depends(oauth2_scheme)):
    """Retrieves the current user from the token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid authentication")
        return username
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication")

@router.get("/transactions/", response_model=List[TransactionResponse])
def get_transactions(db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    """
    Fetch all transactions for the authenticated user.
    """
    return db.query(Transaction).all()

@router.post("/transactions/", response_model=TransactionResponse)
def create_transaction(transaction: TransactionCreate, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    """
    Add a new transaction for the authenticated user.
    """
    new_transaction = Transaction(
        date=transaction.date,
        description=transaction.description,
        amount=transaction.amount,
        category=transaction.category
    )
    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)
    return new_transaction


@router.get("/transactions/{transaction_id}", response_model=TransactionResponse)
def get_transaction(transaction_id: int, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    """
    Fetch a specific transaction by ID for the authenticated user.
    """
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction


@router.put("/transactions/{transaction_id}", response_model=TransactionResponse)
def update_transaction(transaction_id: int, updated_data: TransactionCreate, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    """
    Update a transaction by ID for the authenticated user.
    """
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    transaction.date = updated_data.date
    transaction.description = updated_data.description
    transaction.amount = updated_data.amount
    transaction.category = updated_data.category
    db.commit()
    db.refresh(transaction)
    return transaction


@router.delete("/transactions/{transaction_id}")
def delete_transaction(transaction_id: int, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    """
    Delete a specific transaction by ID for the authenticated user.
    """
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    db.delete(transaction)
    db.commit()
    return {"message": "Transaction deleted successfully"}


@router.post("/transactions/upload/")
def upload_transactions(file: UploadFile = File(...), db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    """
    Upload and process a file of transactions for the authenticated user.
    """
    try:
        # Read file into a pandas DataFrame
        if file.filename.endswith(".csv"):
            df = pd.read_csv(file.file)
        elif file.filename.endswith(".xlsx"):
            df = pd.read_excel(file.file)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format")

        # Process DataFrame and save transactions
        for _, row in df.iterrows():
            category = row.get("category", categorize_transaction(row["description"], db))
            transaction = Transaction(
                date=row["date"],
                description=row["description"],
                amount=row["amount"],
                category=category
            )
            db.add(transaction)

        db.commit()
        return {"message": "Transactions uploaded and categorized successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")


@router.post("/rules/")
def add_rule(keyword: str, category: str, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    # Debug: Print received data
    print(f"Received keyword: {keyword}, category: {category}")

    # Check if rule already exists
    existing_rule = db.query(CategoryRule).filter(CategoryRule.keyword == keyword).first()
    print(f"Existing rule: {existing_rule}")  # Debug: Check existing rule

    if existing_rule:
        raise HTTPException(status_code=400, detail="Rule for this keyword already exists")

    # Add new rule
    rule = CategoryRule(keyword=keyword, category=category)
    db.add(rule)
    db.commit()
    db.refresh(rule)
    print(f"Added rule: {rule}")  # Debug: Confirm rule addition

    return rule

@router.get("/rules/")
def get_rules(db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    rules = db.query(CategoryRule).all()
    return rules

@router.delete("/rules/{rule_id}")
def delete_rule(rule_id: int, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    rule = db.query(CategoryRule).filter(CategoryRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    db.delete(rule)
    db.commit()
    return {"message": "Rule deleted successfully"}

from typing import Optional
from fastapi import Query

@router.get("/transactions/filter/")
def filter_transactions(
        category: Optional[str] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: Optional[str] = Query(None, regex="^(date|amount|category)$"),
        db: Session = Depends(get_db),
        current_user: str = Depends(get_current_user),
):
    """
    Retrieve filtered, searched, and sorted transactions for the authenticated user.
    """
    query = db.query(Transaction)

    # Apply filters
    if category:
        query = query.filter(Transaction.category == category)
    if min_amount:
        query = query.filter(Transaction.amount >= min_amount)
    if max_amount:
        query = query.filter(Transaction.amount <= max_amount)
    if start_date:
        query = query.filter(Transaction.date >= start_date)
    if end_date:
        query = query.filter(Transaction.date <= end_date)
    if search:
        query = query.filter(Transaction.description.ilike(f"%{search}%"))

    # Apply sorting
    if sort_by:
        if sort_by == "date":
            query = query.order_by(Transaction.date)
        elif sort_by == "amount":
            query = query.order_by(Transaction.amount)
        elif sort_by == "category":
            query = query.order_by(Transaction.category)

    return query.all()

@router.get("/transactions/summary/")
def get_transaction_summary(db: Session = Depends(get_db)):
    """
    Get a summary of transactions: total income, total expenses, and net balance.
    """
    total_income = db.query(func.sum(Transaction.amount)).filter(Transaction.amount > 0).scalar() or 0
    total_expenses = db.query(func.sum(Transaction.amount)).filter(Transaction.amount < 0).scalar() or 0
    net_balance = total_income + total_expenses

    return {
        "total_income": total_income,
        "total_expenses": total_expenses,
        "net_balance": net_balance
    }

@router.get("/transactions/category-breakdown/")
def get_category_breakdown(db: Session = Depends(get_db)):
    """
    Get a breakdown of transaction totals by category.
    """
    category_data = (
        db.query(Transaction.category, func.sum(Transaction.amount).label("total"))
        .group_by(Transaction.category)
        .all()
    )

    return [{"category": category, "total": total} for category, total in category_data]

@router.get("/transactions/monthly-trends/")
def get_monthly_trends(db: Session = Depends(get_db)):
    """
    Get monthly income and expense trends.
    """
    monthly_data = (
        db.query(
            func.date_trunc("month", Transaction.date).label("month"),
            func.sum(Transaction.amount).label("total")
        )
        .group_by(func.date_trunc("month", Transaction.date))
        .order_by(func.date_trunc("month", Transaction.date))
        .all()
    )

    income_data = [{"month": month.strftime("%Y-%m"), "total": total} for month, total in monthly_data if total > 0]
    expense_data = [{"month": month.strftime("%Y-%m"), "total": total} for month, total in monthly_data if total < 0]

    return {"income_trends": income_data, "expense_trends": expense_data}

