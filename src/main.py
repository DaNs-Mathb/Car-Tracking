from fastapi import FastAPI
from src.api import main_router


app = FastAPI(docs_url="/docs")
app.include_router(main_router)
