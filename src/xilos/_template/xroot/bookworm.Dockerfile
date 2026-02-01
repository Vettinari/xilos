# Multi-stage build for Debian Bookworm (Slim)
# Dynamic installation argument
ARG INSTALL_GROUP=train,serve

# Build stage
FROM python:3.11-slim-bookworm as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install poetry
RUN pip install poetry

# Copy config
COPY pyproject.toml poetry.lock* ./

# Export requirements dynamically based on build arg
ARG INSTALL_GROUP
RUN poetry export --with ${INSTALL_GROUP} -f requirements.txt --output requirements.txt --without-hashes

# Runtime stage
FROM python:3.11-slim-bookworm

WORKDIR /app

# Install runtime system deps if needed (e.g. libpq for postgres)
# RUN apt-get update && apt-get install -y --no-install-recommends ...

COPY --from=builder /app/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Set dynamic entrypoint script or default
# We can use an env var to decide what to run, or pass the command at runtime
ENV MODULE_NAME=xilos.xtrain.main

CMD ["sh", "-c", "python -m ${MODULE_NAME}"]
