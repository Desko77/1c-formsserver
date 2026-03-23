FROM python:3.12-slim

WORKDIR /app

# Зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Исходники
COPY src/ src/
COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

# Данные
COPY data/ data/
COPY edt_reference/ edt_reference/

# Runtime директория
RUN mkdir -p /databases

ENV PORT=8011
ENV TRANSPORT=streamable-http
ENV DATABASES_PATH=/databases
ENV DATA_PATH=/app/data
ENV EDT_REFERENCE_PATH=/app/edt_reference
ENV EDT_ENABLED=true
ENV EDT_MCP_URL=http://host.docker.internal:9999/sse
ENV EDT_TIMEOUT=10

EXPOSE 8011

CMD ["python", "-m", "mcp_forms"]
