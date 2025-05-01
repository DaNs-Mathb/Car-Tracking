from fastapi import FastAPI
from src.api import main_router
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(docs_url="/docs")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Или конкретные домены ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],  # Разрешаем все методы (POST, GET и т.д.)
    allow_headers=["*"],  # Разрешаем все заголовки
)
app.include_router(main_router)
