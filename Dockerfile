FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app/src

WORKDIR /app

# 1. Python依存をインストール
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel \
 && pip install -r requirements.txt

# 2. アプリ本体をコピー（PHIはGCSから読むのでここには含めない）
COPY src ./src
COPY rag_base ./rag_base

# .env はイメージには焼かず、実行時にホストからマウントする
# ENTRYPOINT: BILL_FOLDER_ID 環境変数を前提にパイプラインを実行
ENTRYPOINT ["python", "-m", "medbill_rag"]
