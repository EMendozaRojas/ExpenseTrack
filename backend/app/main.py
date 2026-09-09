from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.routers import (
    accounts,
    auth,
    budgets,
    categories,
    categorization_rules,
    dashboard,
    expenses,
    fx_rates,
    goals,
    imports,
    insights,
    preferences,
    transactions,
)

settings = get_settings()

app = FastAPI(title="ExpenseTrack API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(categories.router, prefix="/api/v1")
app.include_router(categorization_rules.router, prefix="/api/v1")
app.include_router(accounts.router, prefix="/api/v1")
app.include_router(transactions.router, prefix="/api/v1")
app.include_router(expenses.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")
app.include_router(imports.router, prefix="/api/v1")
app.include_router(budgets.router, prefix="/api/v1")
app.include_router(insights.router, prefix="/api/v1")
app.include_router(goals.router, prefix="/api/v1")
app.include_router(preferences.router, prefix="/api/v1")
app.include_router(fx_rates.router, prefix="/api/v1")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
