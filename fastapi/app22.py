import requests
from fastapi import FastAPI, File, UploadFile, Form, Response
from fastapi.responses import FileResponse
import os

app = FastAPI()

@app.get('/')
def home():
    return {"hello": "World"}

@app.post('/ask')
async def ask(prompt: str = Form(...), file: UploadFile = File(...)):
    # Чтение содержимого файла
    input_content = await file.read()

    # Отправка запроса к серверу Ollama
    res = requests.post(
        'http://ollama:11434/api/generate',
        json={
            "prompt": f"{prompt}\n\n{input_content.decode('utf-8')}",
            "stream": False,
            "model": "qwen2.5-coder:3b"
        }
    )

    # Проверка ответа сервера
    if res.status_code != 200:
        return Response(content=res.text, media_type="application/json", status_code=res.status_code)

    # Создание нового файла с результатами
    output_file_path = "output_result.txt"
    with open(output_file_path, "w") as output_file:
        output_file.write(res.json().get("response", ""))

    # Возврат созданного файла пользователю
    return FileResponse(output_file_path, media_type="text/plain", filename="output_result.txt")
