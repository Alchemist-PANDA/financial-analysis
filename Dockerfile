# Stage 1: Build the Frontend
FROM node:20-slim AS frontend-builder
WORKDIR /app/frontend-next
COPY frontend-next/package*.json ./
RUN npm install --legacy-peer-deps
COPY frontend-next ./
RUN npm run build

# Stage 2: Final Image
FROM python:3.11-slim
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application code
COPY app ./app
COPY config.py .
COPY .env.example .

# Copy built frontend from Stage 1
COPY --from=frontend-builder /app/frontend-next/out ./frontend-next/out

# Expose Hugging Face port
EXPOSE 7860

# Run uvicorn serving both backend and static frontend
CMD ["python", "-m", "uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "7860"]
