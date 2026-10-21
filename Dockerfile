FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HOME=/home/infodesk

WORKDIR /app

COPY requirements.txt ./
RUN python -m pip install --disable-pip-version-check -r requirements.txt \
    && groupadd --gid 10001 infodesk \
    && useradd --uid 10001 --gid 10001 --create-home infodesk \
    && mkdir -p /app/data/backups \
    && chown -R 10001:10001 /app/data

COPY --chown=10001:10001 *.py ./
COPY --chown=10001:10001 deploy/container_start.py deploy/database_backup.py ./
COPY --chown=10001:10001 data/info_service.db ./data/info_service.db

USER 10001:10001

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health', timeout=3).read()"]

ENTRYPOINT ["python", "container_start.py"]
CMD ["python", "-m", "streamlit", "run", "streamlit_app.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true", "--server.fileWatcherType=none", "--browser.gatherUsageStats=false"]
