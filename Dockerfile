# Python 3.11のslimイメージを使用
FROM python:3.11-slim

# 作業ディレクトリの設定
WORKDIR /app

# タイムゾーンを日本に設定
ENV TZ=Asia/Tokyo \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# 依存パッケージのインストール
# Pillowでフォントレンダリングに必要なライブラリをインストール
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    fonts-liberation \
    tzdata \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone \
    && rm -rf /var/lib/apt/lists/*

# 依存関係をインストール（キャッシュを効かせるため先にコピー）
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# プロジェクトファイルをコピー
COPY core/ ./core/
COPY features/ ./features/
COPY fonts/ ./fonts/
COPY bot.py .
COPY main.py .

# 実行ユーザーの設定（セキュリティ向上のため）
# コメントアウト：必要に応じて有効化
# RUN useradd -m -u 1000 botuser && chown -R botuser:botuser /app
# USER botuser

# Botを起動
CMD ["python", "bot.py"]
