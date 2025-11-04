FROM python:3.11-slim
ENV TZ="Europe/Paris"
WORKDIR /app

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY python/ ./python/
COPY scripts/ ./scripts/
COPY sql/ ./sql/
COPY timetables/ ./timetables/
COPY bot.py .
COPY entrypoint.sh .
COPY init.py .

VOLUME ["/app/data", "/app/database"]

RUN chmod +x entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]
