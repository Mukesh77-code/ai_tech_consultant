# Multi-service Production Container for AI Tech Consultant
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV NODE_ENV=production

# Install curl, Node.js 20, and runtime tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    gnupg \
    && mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_20.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list \
    && apt-get update && apt-get install -y --no-install-recommends \
    nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 1. Install Python dependencies
COPY task1_knowledge_brain/requirements.txt task1_requirements.txt
COPY task3_meeting_to_scope/requirements.txt task3_requirements.txt
RUN pip install --no-cache-dir -r task1_requirements.txt -r task3_requirements.txt

# 2. Install Node dependencies
COPY task2_inbox_agent/package*.json ./task2_inbox_agent/
RUN cd task2_inbox_agent && npm install

# 3. Copy application codebase
COPY . .

# 4. Build TypeScript and copy public UI assets
RUN cd task2_inbox_agent && npm run build

# Default environment configuration
ENV PORT=3000
ENV KNOWLEDGE_BRAIN_HOST=127.0.0.1
ENV KNOWLEDGE_BRAIN_PORT=8000
ENV KNOWLEDGE_BRAIN_URL=http://127.0.0.1:8000

EXPOSE 3000
EXPOSE 8000

CMD ["python", "start_production.py"]
