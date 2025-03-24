FROM python:3.11-slim

WORKDIR /app

# 必要なパッケージをインストール
RUN apt-get update && apt-get install -y sqlite3 && apt-get clean && rm -rf /var/lib/apt/lists/*

# Pythonパッケージをインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードをコピー（修正：srcフォルダを作成してコピー）
COPY src/ /app/src/
COPY requirements.txt /app/

# データベースディレクトリを作成（ボリュームマウント用）
RUN mkdir -p /data
VOLUME ["/data"]

# タイムゾーンを設定（日本時間に設定）
ENV TZ=Asia/Tokyo

# 実行コマンド（修正：パスを変更）
CMD ["python", "src/rss_bot.py"]