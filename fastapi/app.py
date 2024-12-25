import requests
from fastapi import FastAPI, File, UploadFile, Form, Response, Body, HTTPException
from typing import List
import os
import time

app = FastAPI()

# Директория для сохранения файлов
RESULT_DIR = "/root/Documents/result"
os.makedirs(RESULT_DIR, exist_ok=True)

@app.get('/')
def home():
    """
       Возвращает приветственное сообщение для проверки работы API.
       """
    return {"hello": "World"}




@app.get('/ask')
def ask(prompt :str):
    """
        Принимает строку prompt в теле запроса, отправляет её в модель для обработки
        и возвращает результат в формате JSON.
        """
    res = requests.post('http://ollama:11434/api/generate', json={
        "prompt": prompt,
        "stream" : False,
        "model" : "qwen2.5-coder:3b"
    })

    return Response(content=res.text, media_type="application/json")


@app.post('/generate_sql')
async def generate_sql(files: List[UploadFile] = File(...)):
    """
    Принимает массив файлов с запросами Firebird SQL, преобразует их в формат PostgreSQL
    и сохраняет каждый результат в отдельный файл.
    """
    results = []

    for file in files:
        start_time = time.time()
        input_content = await file.read()
        file_name = os.path.splitext(file.filename)[0]

        # Подробный prompt для генерации SQL
        detailed_prompt = (
            "Convert the given Firebird SQL query into PostgreSQL syntax while preserving its original logic. "
            "Apply PostgreSQL-specific rules and best practices.\n\n"
            "Output the following in a single SQL file:\n"
            "1. The original Firebird SQL query, commented at the beginning of the file, for reference.\n"
            "2. The translated PostgreSQL query, with detailed comments explaining:\n"
            "   - Changes made to adapt to PostgreSQL syntax.\n"
            "   - Differences in data types, constructs, or functions, if applicable.\n\n"
            "Ensure that the translated query maintains the same functionality and intent as the original."
        )

        # Отправка запроса к серверу Ollama для SQL
        res = requests.post(
            'http://ollama:11434/api/generate',
            json={
                "prompt": f"{detailed_prompt}\n\n{input_content.decode('utf-8')}",
                "stream": False,
                "model": "qwen2.5-coder:3b"
            }
        )

        if res.status_code != 200:
            return Response(content=res.text, media_type="application/json", status_code=res.status_code)

        sql_file_path = os.path.join(RESULT_DIR, f"{file_name}.sql")
        with open(sql_file_path, "w") as sql_file:
            sql_file.write(res.json().get("response", ""))

        end_time = time.time()
        print(f"Time taken for API call for {file.filename}: {end_time - start_time} seconds")

        results.append({"file": file.filename, "sql_file": sql_file_path})

    return {"message": "SQL files created successfully", "results": results}

@app.post('/generate_tests')
async def generate_tests(files: List[UploadFile] = File(...)):
    """
    Принимает массив файлов с запросами PostgreSQL и генерирует тестовые SQL-файлы
    для проверки корректности запросов.
    """
    results = []

    for file in files:
        input_content = await file.read()
        file_name = os.path.splitext(file.filename)[0]

        # Подробный prompt для генерации тестов
        detailed_prompt = (
            "Generate a set of test cases for the given PostgreSQL query. "
            "The input query is a translated version of a Firebird SQL query.\n\n"
            "Output the following in a test SQL file:\n"
            "1. A detailed comment at the top explaining the purpose of the tests.\n"
            "2. A test to verify the existence of the target table or structure, using PostgreSQL's information_schema.\n"
            "3. A test to validate the syntax and execution plan of the query using EXPLAIN.\n"
            "4. Optional example test cases that validate the correctness of the query's results, such as:\n"
            "   - Expected row counts.\n"
            "   - Verifying specific output fields or conditions.\n\n"
            "Ensure that each test includes clear comments to explain its purpose and how it relates to the original query."
        )

        # Отправка запроса к серверу Ollama для тестов
        res = requests.post(
            'http://ollama:11434/api/generate',
            json={
                "prompt": f"{detailed_prompt}\n\n{input_content.decode('utf-8')}",
                "stream": False,
                "model": "qwen2.5-coder:3b"
            }
        )

        if res.status_code != 200:
            return Response(content=res.text, media_type="application/json", status_code=res.status_code)

        test_file_path = os.path.join(RESULT_DIR, f"{file_name}_test.sql")
        with open(test_file_path, "w") as test_file:
            test_file.write(res.json().get("response", ""))

        results.append({"file": file.filename, "test_file": test_file_path})

    return {"message": "Test files created successfully", "results": results}
