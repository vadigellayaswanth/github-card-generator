FROM python:3.11-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN uv pip install --no-cache -r requirements.txt --system

COPY . .

EXPOSE 8000

CMD ["python", "main.py"]
