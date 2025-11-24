FROM python:3.11-slim

WORKDIR /app

# Install git for update functionality
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY bot.py .
COPY cogs/ ./cogs/
COPY utils/ ./utils/
COPY data/ ./data/

# Run bot
CMD ["python", "bot.py"]
