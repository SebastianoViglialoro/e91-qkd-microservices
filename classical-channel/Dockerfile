FROM python:3.12-slim

WORKDIR /app
COPY classical-channel/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY classical-channel/app ./app
COPY shared/__init__.py ./shared/__init__.py
COPY shared/bases.py ./shared/bases.py
EXPOSE 8008
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8008"]
