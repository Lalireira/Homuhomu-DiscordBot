# Python 3.11のslimイメージを使用
FROM python:3.11-slim

# 作業ディレクトリの設定
WORKDIR /app

# タイムゾーンを日本に設定（オプション）
ENV TZ=Asia/Tokyo

# 依存パッケージのインストール
# Pillowでフォントレンダリングに必要なライブラリをインストール
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# requirements.txtをコピーして依存関係をインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# プロジェクトファイルをコピー
COPY . .

# Botを起動
CMD ["python", "bot.py"]