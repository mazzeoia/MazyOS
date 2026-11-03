FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir uv==0.8.14

COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-dev

COPY app/ app/

EXPOSE 8000
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
