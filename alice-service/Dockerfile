FROM python:3.12-slim

WORKDIR /app
COPY alice-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY alice-service/app ./app
COPY shared/__init__.py ./shared/__init__.py
COPY shared/bases.py ./shared/bases.py
EXPOSE 8005
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8005"]
