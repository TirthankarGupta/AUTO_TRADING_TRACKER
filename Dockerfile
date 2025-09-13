FROM python:3.11-bullseye

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# system dependencies for scientific packages
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    make \
    libffi-dev \
    libssl-dev \
    curl \
    git \
    libfreetype6-dev \
    libpng-dev \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# copy requirements first (better caching)
COPY requirements.txt .

# install pip packages
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# copy project files
COPY . .

EXPOSE 8501

CMD ["streamlit","run","trading_dashboard.py","--server.port","8501","--server.address","0.0.0.0"]
