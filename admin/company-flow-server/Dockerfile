# Stage 1: Build React frontend
FROM node:20-slim AS frontend-builder
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend ./
RUN npm run build

# Stage 2: Build Python API
FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

COPY pyproject.toml README.md ./
COPY src ./src
COPY --from=frontend-builder /frontend/dist ./frontend_dist

RUN pip install --no-cache-dir .

COPY flows ./flows
RUN mkdir -p /data/team_registry

ENV CREW_REGISTRY_ROOT=/data/team_registry FLOW_ROOT=/app/flows
CMD ["uvicorn","company_flow_server.app:app","--host","0.0.0.0","--port","8080"]
