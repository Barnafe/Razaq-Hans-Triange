# Multi-stage build so the final image only needs Python at runtime --
# Node is only used to compile the frontend into static files.

# ---- Stage 1: build the React frontend ----
FROM node:20-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build
# Produces /app/frontend/dist -- exactly what backend/app/main.py looks
# for at os.path.join(__file__, "..", "..", "frontend", "dist")

# ---- Stage 2: Python backend, serving the built frontend too ----
FROM python:3.11-slim
WORKDIR /app

COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend/ backend/
COPY --from=frontend-build /app/frontend/dist frontend/dist

# Render sets $PORT at runtime and routes external traffic to it -- do
# not hardcode 8000 here. --host 0.0.0.0 is required so Render's proxy
# (running outside this container) can reach the server.
EXPOSE 8000
CMD ["sh", "-c", "uvicorn main:app --app-dir backend/app --host 0.0.0.0 --port ${PORT:-8000}"]
