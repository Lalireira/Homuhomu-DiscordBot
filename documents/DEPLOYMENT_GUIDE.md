# デプロイメントガイド

このドキュメントでは、homuhomu-discordbotを各種クラウドサービスにデプロイする方法を説明します。

---

## 📋 目次

1. [Railway（最推奨）](#1-railway最推奨)
2. [Oracle Cloud（完全無料）](#2-oracle-cloud完全無料)
3. [AWS ECS (Fargate)](#3-aws-ecs-fargate)
4. [Render](#4-render)
5. [AWS Lightsail / EC2](#5-aws-lightsail--ec2)
6. [環境変数の設定](#環境変数の設定)

---

## 1. Railway（最推奨）

### 特徴
- ✅ 月$5の無料クレジット
- ✅ GitHub連携で自動デプロイ
- ✅ Dockerfileをそのまま使用
- ✅ 簡単な環境変数管理
- ✅ 自動再起動機能

### デプロイ手順

詳細は [QUICK_START_DEPLOY.md](./QUICK_START_DEPLOY.md) を参照してください。

#### Step 1: アカウント作成
1. [Railway](https://railway.app/)にアクセス
2. 「Start a New Project」をクリック
3. GitHubアカウントで認証

#### Step 2: プロジェクト作成
1. 「New Project」→「Deploy from GitHub repo」を選択
2. 該当のGitHubリポジトリを選択
3. Railwayが自動的にDockerfileを検出

#### Step 3: 環境変数の設定
1. プロジェクトの「Variables」タブを開く
2. 必要な環境変数を追加（下記の「環境変数の設定」セクション参照）

#### Step 4: デプロイ
- 環境変数を設定すると自動的にデプロイが開始されます
- 「Deployments」タブでログを確認できます

### コスト見積もり
- 月$5の無料クレジット内で収まる可能性が高い
- 超過する場合は従量課金（目安: $5-10/月）

---

## 2. Oracle Cloud（完全無料）

### 特徴
- ✅ **永久無料**（Free Tierが期限なし）
- ✅ VM.Standard.E2.1.Micro × 2台まで無料
- ✅ 完全なコントロール
- ⚠️ 初期設定がやや複雑

### デプロイ手順

#### 自動セットアップスクリプトを使用（推奨）

```bash
# インスタンスにSSH接続後、リポジトリをクローン
git clone https://github.com/<your-username>/homuhomu-discordbot.git
cd homuhomu-discordbot

# セットアップスクリプトを実行
chmod +x deploy/setup-oracle-cloud.sh
./deploy/setup-oracle-cloud.sh

# .envファイルを作成
nano .env
# 環境変数を記入して保存

# 起動
docker-compose up -d
```

詳細な手動セットアップ手順については、プロジェクトリポジトリのドキュメントを参照してください。

---

## 3. AWS ECS (Fargate)

### 特徴
- ✅ サーバーレス（サーバー管理不要）
- ✅ Dockerネイティブ
- ✅ 高い信頼性とスケーラビリティ
- ✅ CloudWatch統合（ログ・メトリクス）
- ⚠️ 初期設定がやや複雑
- ⚠️ 月$7-10程度のコスト

### 詳細ガイド

**完全なガイド**: [DEPLOYMENT_ECS_FARGATE.md](./DEPLOYMENT_ECS_FARGATE.md)

### クイックスタート

#### 1. 初期セットアップ

```bash
# AWS CLIがインストール済みで、認証情報が設定されていることを確認
aws configure

# 自動セットアップスクリプトを実行
chmod +x deploy/setup-ecs-fargate.sh
./deploy/setup-ecs-fargate.sh
```

#### 2. 環境変数の設定（AWS Secrets Manager）

```bash
# 各シークレットを作成
aws secretsmanager create-secret \
    --name homuhomu-bot/discord-token \
    --secret-string "your_actual_discord_bot_token" \
    --region ap-northeast-1

# 他の環境変数も同様に作成（詳細はDEPLOYMENT_ECS_FARGATE.mdを参照）
```

#### 3. タスク定義の登録

```bash
aws ecs register-task-definition \
    --cli-input-json file://deploy/ecs-task-definition.json \
    --region ap-northeast-1
```

#### 4. イメージのビルドとデプロイ

```bash
chmod +x deploy/deploy-to-ecs.sh
./deploy/deploy-to-ecs.sh
```

#### 5. サービスの作成

```bash
aws ecs create-service \
    --cluster homuhomu-bot-cluster \
    --service-name homuhomu-bot-service \
    --task-definition homuhomu-bot-task \
    --desired-count 1 \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[subnet-xxxxx],securityGroups=[sg-xxxxx],assignPublicIp=ENABLED}" \
    --region ap-northeast-1
```

### コスト見積もり

**最小スペック（0.25 vCPU、0.5GB メモリ）:**
- 約$10/月

### GitHub Actionsでの自動デプロイ

`.github/workflows/deploy-ecs.yml`が用意されています。GitHubにAWSの認証情報を設定すれば、pushで自動デプロイされます。

---

## 4. Render

### 特徴
- ✅ 750時間/月の無料枠
- ⚠️ 無料プランは15分無通信でスリープ（Bot向けではない）
- ✅ 有料プラン（$7/月）で常時稼働

### デプロイ手順

#### Step 1: アカウント作成
1. [Render](https://render.com/)にアクセス
2. GitHubアカウントで認証

#### Step 2: 新規サービス作成
1. 「New」→「Web Service」を選択
2. GitHubリポジトリを選択
3. 以下の設定:
   - **Environment**: Docker
   - **Plan**: Free または Starter（$7/月）

#### Step 3: 環境変数設定
- 「Environment」タブで環境変数を追加

#### 注意点
- **無料プランではスリープする**ため、Discordボットには不向き
- 常時稼働には有料プラン（$7/月）が必要

---

## 5. AWS Lightsail / EC2

### 特徴
- ✅ 高い安定性
- ✅ EC2は12ヶ月無料（t2.micro）
- ✅ Lightsailは$3.5/月〜
- ⚠️ やや複雑な設定

### デプロイ手順（EC2 t2.micro - 12ヶ月無料）

#### 自動セットアップスクリプトを使用（推奨）

```bash
# EC2インスタンスにSSH接続後
git clone https://github.com/<your-username>/homuhomu-discordbot.git
cd homuhomu-discordbot

# セットアップスクリプトを実行
chmod +x deploy/setup-aws-ec2.sh
./deploy/setup-aws-ec2.sh

# .envファイルを作成
nano .env
# 環境変数を記入

# 起動
docker-compose up -d
```

---

## 環境変数の設定

すべてのデプロイ方法で、以下の環境変数が必要です：

### 必須環境変数

```env
# Discord Bot Token（必須）
DISCORD_BOT_TOKEN=your_discord_bot_token

# osu! API認証情報（/wrapped コマンド用）
OSU_CLIENT_ID=your_osu_client_id
OSU_CLIENT_SECRET=your_osu_client_secret

# Twitch API認証情報（Twitch配信通知機能用）
TWITCH_CLIENT_ID=your_twitch_client_id
TWITCH_CLIENT_SECRET=your_twitch_client_secret
TWITCH_CHANNEL_NAME=target_channel_name

# Discord設定
TWITCH_NOTIFICATION_CHANNEL_ID=discord_channel_id_for_notifications
NOTIFICATION_ROLE_ID=discord_role_id_for_notifications
```

### 環境変数の取得方法

#### DISCORD_BOT_TOKEN
1. [Discord Developer Portal](https://discord.com/developers/applications)
2. アプリケーションを選択
3. 「Bot」タブ → 「Token」をコピー

#### OSU_CLIENT_ID / OSU_CLIENT_SECRET
1. [osu! Settings](https://osu.ppy.sh/home/account/edit#oauth)
2. 「New OAuth Application」
3. Callback URLは適当でOK（例: `http://localhost`）

#### TWITCH_CLIENT_ID / TWITCH_CLIENT_SECRET
1. [Twitch Developer Console](https://dev.twitch.tv/console/apps)
2. 「Register Your Application」
3. OAuth Redirect URLは `http://localhost` でOK

---

## 💰 コスト比較

| サービス | 月額コスト | 常時稼働 | 設定難易度 | 推奨度 |
|---------|----------|---------|----------|-------|
| **Railway** | $5無料枠内 | ✅ | ★☆☆☆☆ | ★★★★★ |
| **Oracle Cloud** | **完全無料** | ✅ | ★★★☆☆ | ★★★★★ |
| **AWS ECS Fargate** | $10程度 | ✅ | ★★★☆☆ | ★★★★☆ |
| **Render（無料）** | 無料 | ❌ スリープあり | ★☆☆☆☆ | ★★☆☆☆ |
| **Render（有料）** | $7〜 | ✅ | ★☆☆☆☆ | ★★★☆☆ |
| **AWS EC2（無料枠）** | 12ヶ月無料 | ✅ | ★★★☆☆ | ★★★★☆ |
| **AWS Lightsail** | $3.5〜 | ✅ | ★★☆☆☆ | ★★★★☆ |

---

## 🎯 推奨デプロイ方法

### 初心者 / 簡単さ重視
→ **Railway**（GitHubと連携して5分でデプロイ完了）

### コスト重視 / 永久無料
→ **Oracle Cloud**（完全無料だが初期設定がやや複雑）

### AWS経験者 / サーバーレス重視
→ **AWS ECS (Fargate)**（サーバー管理不要、月$10程度）

### AWS経験者 / コスト重視
→ **AWS EC2**（12ヶ月無料、その後は月$3-5程度）

---

## 📊 監視とログ

### Railway
- ダッシュボードでリアルタイムログ確認可能
- メトリクス（CPU、メモリ）も表示

### AWS ECS (Fargate)
```bash
# CloudWatch Logsでログを確認
aws logs tail /ecs/homuhomu-bot --follow --region ap-northeast-1
```

### Oracle Cloud / AWS EC2
```bash
# ログ確認
docker-compose logs -f

# コンテナステータス確認
docker-compose ps

# リソース使用状況
docker stats
```

---

## 🔄 アップデート方法

### Railway（自動）
- GitHubにpushすると自動的に再デプロイ

### AWS ECS (Fargate)
```bash
# デプロイスクリプトを実行
./deploy/deploy-to-ecs.sh
```

または、GitHub Actionsで自動デプロイ

### Oracle Cloud / AWS EC2（手動）
```bash
cd ~/homuhomu-discordbot
git pull
docker-compose up -d --build
```

---

## まとめ

- **簡単にすぐ始めたい**: → **Railway**
- **完全無料で使いたい**: → **Oracle Cloud**
- **AWSでサーバーレス**: → **ECS (Fargate)**
- **AWSでコスト重視**: → **EC2（12ヶ月無料）**

どの方法を選んでも、既存のDockerfileとdocker-compose.ymlをそのまま使用できます！


