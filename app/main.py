from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from app.bid.routers import router as bid_router
from app.user.routers import router as user_router
from app.tender.routers import router as tender_router
from app.organization.routers import router as organization_router


app = FastAPI(title="Avito2024", root_path="/api")

app.include_router(user_router)
app.include_router(organization_router)
app.include_router(tender_router)
app.include_router(bid_router)


@app.get("/", include_in_schema=False)
def index():
    return RedirectResponse("/docs")


@app.get("/ping")
def ping() -> str:
    return "ok"
