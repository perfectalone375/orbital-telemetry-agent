FROM python:3.12-slim AS base
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY pyproject.toml README.md LICENSE /app/
COPY src/ /app/src/
COPY tests/ /app/tests/
RUN pip install --upgrade pip && pip install ".[dev]"

FROM base AS test
CMD ["pytest", "-v", "tests/"]

FROM base AS runtime
ENTRYPOINT ["orbitctl"]
CMD ["--help"]
