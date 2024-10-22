# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.10-slim

ENV TZ Asia/Kolkata

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Install pip requirements
COPY requirements.txt .
RUN python -m pip install -r requirements.txt

WORKDIR /app

COPY . .

CMD ["streamlit", "run", "main.py", "--server.port=8080", "--server.address=0.0.0.0"]

EXPOSE 8080