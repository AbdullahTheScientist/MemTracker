FROM ultralytics/ultralytics:latest-py3

WORKDIR /app

# Copy only your code + requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
