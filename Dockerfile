FROM python:3.11-slim
WORKDIR /app

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Europe/Paris

RUN apt-get update && apt-get install -y --no-install-recommends tzdata \
    && ln -fs /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY python/ ./python/
COPY scripts/ ./scripts/
COPY logs/ ./logs/
COPY sql/ ./sql/
COPY timetables/ ./timetables/
COPY bot.py .
COPY entrypoint.sh .
COPY init.py .

VOLUME ["/app/data", "/app/database"]

RUN chmod +x entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]
