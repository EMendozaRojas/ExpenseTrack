from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.core.openapi import API_DESCRIPTION, API_TITLE, API_VERSION, OPENAPI_TAGS, Tag
from app.routers import (
    accounts,
    attachments,
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
    notifications,
    preferences,
    transactions,
    users,
)

settings = get_settings()

app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    description=API_DESCRIPTION,
    openapi_tags=OPENAPI_TAGS,
    swagger_ui_parameters={"persistAuthorization": True},
)

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
app.include_router(attachments.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(notifications.router, prefix="/api/v1")


class HealthStatus(BaseModel):
    status: str = Field(description="`ok` si el servicio responde.", examples=["ok"])


@app.get("/health", tags=[Tag.SISTEMA], summary="Comprobar el estado del servicio")
def health() -> HealthStatus:
    """Responde `ok` si la API está en marcha. No requiere autenticación ni
    comprueba la base de datos."""
    return HealthStatus(status="ok")
