from fastapi import FastAPI
import logging
from app.routes import transactions
from app.database import engine
from app.models import Base

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("financeflare")

app = FastAPI(title="FinanceFlare Backend")

def create_tables():
    Base.metadata.create_all(bind=engine)

@app.on_event("startup")
def on_startup():
    create_tables()

app.include_router(transactions.router)
logger.info("Router included successfully!")

@app.get("/")
def root():
    return {"message": "Welcome to the FinanceFlare API!"}

def create_tables():
    Base.metadata.create_all(bind=engine)
