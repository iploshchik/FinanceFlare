from sqlalchemy.orm import Session
from app.models import CategoryRule

def categorize_transaction(description: str, db: Session) -> str:
    # Check user-defined rules
    user_rules = db.query(CategoryRule).all()
    for rule in user_rules:
        if rule.keyword.lower() in description.lower():
            return rule.category

    # Default rules
    categories = {
        "shopping": ["Amazon", "Walmart", "Target"],
        "income": ["Salary", "Bonus", "Freelance"],
        "transportation": ["Uber", "Lyft", "Gas"],
        "entertainment": ["Netflix", "Spotify", "Cinema"],
        "groceries": ["Whole Foods", "Trader Joe's", "Kroger"],
    }

    for category, keywords in categories.items():
        if any(keyword.lower() in description.lower() for keyword in keywords):
            return category

    return "uncategorized"
