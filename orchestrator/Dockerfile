FROM python:3.12-slim

WORKDIR /app
COPY orchestrator/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY orchestrator/app ./app
COPY shared/__init__.py ./shared/__init__.py
COPY shared/outcome_sampler.py ./shared/outcome_sampler.py
EXPOSE 8001
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
