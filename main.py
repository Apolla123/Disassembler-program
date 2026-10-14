from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from decoder import generate_listing


app = FastAPI()


# Описываем данные, которые получим от пользователя
class CodeInput(BaseModel):
    machine_code: str


# Главная страница сайта
@app.get("/", response_class=HTMLResponse)
def index():
    with open("templates/index.html", "r", encoding="utf-8") as file:
        return file.read()


@app.post("/decode")
def decode_code(data: CodeInput):
    listing = generate_listing(data.machine_code)

    return {"listing": listing}


# Команда для запуска сервера:
# python -m uvicorn main:app --reload --port 8002