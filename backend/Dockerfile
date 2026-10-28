FROM python:3.13-slim

# Install Astral uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

# Copy dependency definitions and lockfile first for Docker layer caching
COPY pyproject.toml uv.lock ./

# Install dependencies into virtualenv without dev packages
RUN uv sync --frozen --no-dev --no-install-project

# Copy application source code and docs
COPY src ./src
COPY docs/openapi.yaml ./docs/openapi.yaml

# Sync the project itself
RUN uv sync --frozen --no-dev

# Add virtual environment to PATH
ENV PATH="/app/.venv/bin:$PATH"

RUN mkdir -p uploads logs \
    && useradd --create-home --uid 1000 appuser \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8001

CMD ["uv", "run", "python", "-m", "src.server"]

