# Multi-stage build
FROM python:3.11-alpine as builder

WORKDIR /app

# Install build dependencies
RUN apk add --no-cache build-base

# Install poetry
RUN pip install poetry

# Copy config
COPY pyproject.toml poetry.lock* ./

# Export requirements - install ALL groups by default for simplicity in base image.
# For production, you might want separate stages for 'train' and 'serve'.
RUN poetry export --with train,serve -f requirements.txt --output requirements.txt --without-hashes

# Runtime stage
FROM python:3.11-alpine

WORKDIR /app

COPY --from=builder /app/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Default entrypoint (can be overridden)
# Example: docker run xilos python -m xilos.xtrain.main
# Example: docker run xilos python -m xilos.xserve.main
CMD ["python", "-m", "xilos.xtrain.main"]
