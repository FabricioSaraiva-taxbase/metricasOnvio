# Usa Python leve
FROM python:3.10-slim

# Define pasta de trabalho
WORKDIR /app

# 1. Instala Poppler e Tesseract (Essencial para o OCR funcionar no Linux)
RUN apt-get update && apt-get install -y \
    poppler-utils \
    tesseract-ocr \
    libtesseract-dev \
    && rm -rf /var/lib/apt/lists/*

# 2. Instala as bibliotecas Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. Copia TODO o seu código e credenciais para dentro
COPY . .

# 4. Comando: Executa o job de auditoria fiscal
CMD ["python", "main.py"]