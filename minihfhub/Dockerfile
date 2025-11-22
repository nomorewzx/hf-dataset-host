FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY minihfhub ./minihfhub

ENV DATABASE_URL=sqlite:///./data/minihfhub.db \
    GITEA_API_BASE=http://gitea:3000/api/v1 \
    GITEA_RAW_BASE=http://gitea:3000

EXPOSE 8000

CMD ["uvicorn", "minihfhub.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
