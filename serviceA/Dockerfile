FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install starlette aio-pika uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9000"]
