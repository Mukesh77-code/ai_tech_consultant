# Multi-service Production Container for AI Tech Consultant
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install curl, ca-certificates, and Node.js 20 via official NodeSource script
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 1. Install Python dependencies
COPY task1_knowledge_brain/requirements.txt task1_requirements.txt
COPY task3_meeting_to_scope/requirements.txt task3_requirements.txt
RUN pip install --no-cache-dir -r task1_requirements.txt -r task3_requirements.txt httpx

# 2. Copy application codebase
COPY . .

# 3. Install Node.js dependencies and build Task 2
RUN cd task2_inbox_agent && npm install && npm run build

# Default runtime configuration
ENV NODE_ENV=production
ENV PORT=10000
ENV KNOWLEDGE_BRAIN_HOST=127.0.0.1
ENV KNOWLEDGE_BRAIN_PORT=8000
ENV KNOWLEDGE_BRAIN_URL=http://127.0.0.1:8000

EXPOSE 10000
EXPOSE 8000

CMD ["python", "start_production.py"]
