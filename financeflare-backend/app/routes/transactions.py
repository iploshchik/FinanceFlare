from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from fastapi import UploadFile, File
import pandas as pd
from app.database import get_db
from app.models import Transaction, TransactionCreate, TransactionResponse, CategoryRule
from app.services.categorization import categorize_transaction

router = APIRouter()

@router.get("/transactions/", response_model=List[TransactionResponse])
def get_transactions(db: Session = Depends(get_db)):
    transactions = db.query(Transaction).all()
    return transactions

@router.post("/transactions/", response_model=TransactionResponse)
def create_transaction(transaction: TransactionCreate, db: Session = Depends(get_db)):
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
def get_transaction(transaction_id: int, db: Session = Depends(get_db)):
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction

@router.put("/transactions/{transaction_id}", response_model=TransactionResponse)
def update_transaction(transaction_id: int, updated_data: TransactionCreate, db: Session = Depends(get_db)):
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
def delete_transaction(transaction_id: int, db: Session = Depends(get_db)):
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    db.delete(transaction)
    db.commit()
    return {"message": "Transaction deleted successfully"}

@router.post("/transactions/upload/")
def upload_transactions(file: UploadFile = File(...), db: Session = Depends(get_db)):
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
            # Use categorization logic if 'category' is not provided
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
def add_rule(keyword: str, category: str, db: Session = Depends(get_db)):
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
def get_rules(db: Session = Depends(get_db)):
    rules = db.query(CategoryRule).all()
    return rules

@router.delete("/rules/{rule_id}")
def delete_rule(rule_id: int, db: Session = Depends(get_db)):
    rule = db.query(CategoryRule).filter(CategoryRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    db.delete(rule)
    db.commit()
    return {"message": "Rule deleted successfully"}