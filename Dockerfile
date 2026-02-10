# 1. Usa uma imagem base do Python leve
FROM python:3.9-slim

# 2. Define a pasta de trabalho dentro do conteiner
WORKDIR /app

# 3. Copia os arquivos necessários para dentro da nuvem
# (O script, os requisitos, a chave de acesso e o Excel de clientes)
COPY requirements.txt .
COPY app_metricas.py .
COPY service_account.json .
COPY statusContatos.xlsx .
COPY logo_taxbase.png .

# 4. Instala as bibliotecas
RUN pip install --no-cache-dir -r requirements.txt

# 5. Expõe a porta que o Cloud Run espera (8080)
EXPOSE 8080

# 6. Comando para rodar o app quando o site ligar
# Configura para ouvir na porta 8080
CMD ["streamlit", "run", "app_metricas.py", "--server.port=8080", "--server.address=0.0.0.0"]