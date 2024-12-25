import requests
from fastapi import FastAPI, File, UploadFile, Form, Response
from fastapi.responses import FileResponse
import os

app = FastAPI()

# Путь для сохранения файлов
RESULT_DIR = "/root/Documents/result"

# Убедимся, что директория существует
os.makedirs(RESULT_DIR, exist_ok=True)


@app.get('/')
def home():
    return {"hello": "World"}


@app.post('/ask')
async def ask(prompt: str = Form(...), file: UploadFile = File(...)):
    # Чтение содержимого файла
    input_content = await file.read()

    # Имя файла без расширения
    file_name = os.path.splitext(file.filename)[0]

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

    # Получение результата из ответа
    response_content = res.json().get("response", "")

    # Пути для файлов
    sql_file_path = os.path.join(RESULT_DIR, f"{file_name}.sql")
    test_file_path = os.path.join(RESULT_DIR, f"{file_name}_test.sql")

    # Сохранение основного SQL-запроса
    with open(sql_file_path, "w") as sql_file:
        sql_file.write(response_content)

    # Создание тестового файла
    with open(test_file_path, "w") as test_file:
        test_file.write(f"-- Test cases for {file_name}\n")
        test_file.write("SELECT * FROM information_schema.tables WHERE table_name = 'test_table';\n")
        test_file.write(f"EXPLAIN {response_content};\n")

    # Возврат результата
    return {
        "message": "Files created successfully",
        "sql_file": sql_file_path,
        "test_file": test_file_path
    }
