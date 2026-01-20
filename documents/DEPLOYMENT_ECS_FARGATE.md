# AWS ECS (Fargate) デプロイガイド

このガイドでは、AWS ECS (Fargate)を使用してDiscordボットをデプロイする方法を説明します。

---

## 📋 目次

1. [ECS (Fargate)とは](#ecs-fargateとは)
2. [料金について](#料金について)
3. [前提条件](#前提条件)
4. [デプロイ手順](#デプロイ手順)
5. [自動化スクリプト](#自動化スクリプト)
6. [トラブルシューティング](#トラブルシューティング)

---

## ECS (Fargate)とは

### 特徴

- ✅ **サーバーレス**: EC2インスタンスの管理不要
- ✅ **スケーラブル**: 必要に応じて自動スケーリング
- ✅ **Dockerネイティブ**: 既存のDockerfileをそのまま使用
- ✅ **高可用性**: AWSの信頼性
- ✅ **CloudWatch統合**: ログとメトリクスを自動収集
- ⚠️ **やや複雑**: 初期設定に時間がかかる

### 他サービスとの比較

| 項目 | ECS Fargate | EC2 | Railway |
|-----|------------|-----|---------|
| サーバー管理 | 不要 | 必要 | 不要 |
| 月額コスト | $7-10 | $3.5-10 | $5無料枠 |
| 設定難易度 | ★★★☆☆ | ★★★☆☆ | ★☆☆☆☆ |
| スケーリング | 自動 | 手動 | 自動 |
| 信頼性 | ★★★★★ | ★★★★☆ | ★★★★☆ |

---

## 料金について

### Fargate料金（東京リージョン）

**推奨スペック: 0.25 vCPU、0.5GB メモリ**

- **vCPU**: $0.04656 per vCPU per hour
- **メモリ**: $0.00511 per GB per hour

**月額料金（24時間365日稼働）:**
```
vCPU: 0.25 × $0.04656 × 24 × 30 = $8.38
メモリ: 0.5 × $0.00511 × 24 × 30 = $1.84
合計: 約 $10.22/月
```

**最小スペック: 0.25 vCPU、0.5GB メモリ（上記と同じ）**

### 追加コスト

- **ECR（コンテナレジストリ）**: 最初の500MB/月は無料
- **CloudWatch Logs**: 最初の5GB/月は無料
- **データ転送**: 通常のDiscordボットなら無料枠内

### 無料枠（12ヶ月）

AWS無料利用枠には**Fargateは含まれません**が、以下が無料：
- CloudWatch Logs: 5GB/月
- ECR: 500MB/月

---

## 前提条件

### 必要なもの

1. **AWSアカウント**
2. **AWS CLI** (ローカルにインストール)
3. **Docker** (ローカルにインストール)
4. **環境変数の準備** (DISCORD_BOT_TOKEN等)

### AWS CLIのインストール

#### Windows
```powershell
# Chocolateyを使用
choco install awscli

# または公式インストーラーをダウンロード
# https://aws.amazon.com/cli/
```

#### macOS
```bash
brew install awscli
```

#### Linux
```bash
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
```

### AWS CLIの設定

```bash
aws configure
# AWS Access Key ID: あなたのアクセスキー
# AWS Secret Access Key: あなたのシークレットキー
# Default region name: ap-northeast-1 (東京)
# Default output format: json
```

---

## デプロイ手順

### Step 1: ECRリポジトリの作成

```bash
# ECRリポジトリを作成
aws ecr create-repository \
    --repository-name homuhomu-discordbot \
    --region ap-northeast-1

# 出力からrepositoryUriをメモ
# 例: 123456789012.dkr.ecr.ap-northeast-1.amazonaws.com/homuhomu-discordbot
```

### Step 2: Dockerイメージのビルドとプッシュ

```bash
# ECRにログイン
aws ecr get-login-password --region ap-northeast-1 | \
    docker login --username AWS --password-stdin \
    123456789012.dkr.ecr.ap-northeast-1.amazonaws.com

# Dockerイメージをビルド
docker build -t homuhomu-discordbot .

# イメージにタグ付け
docker tag homuhomu-discordbot:latest \
    123456789012.dkr.ecr.ap-northeast-1.amazonaws.com/homuhomu-discordbot:latest

# ECRにプッシュ
docker push 123456789012.dkr.ecr.ap-northeast-1.amazonaws.com/homuhomu-discordbot:latest
```

### Step 3: ECSクラスターの作成

```bash
# ECSクラスターを作成
aws ecs create-cluster \
    --cluster-name homuhomu-bot-cluster \
    --region ap-northeast-1
```

### Step 4: タスク定義の作成

`ecs-task-definition.json`ファイルを作成します（後述のファイルを参照）。

```bash
# タスク定義を登録
aws ecs register-task-definition \
    --cli-input-json file://deploy/ecs-task-definition.json \
    --region ap-northeast-1
```

### Step 5: サービスの作成

```bash
# サービスを作成（パブリックIPを使用する場合）
aws ecs create-service \
    --cluster homuhomu-bot-cluster \
    --service-name homuhomu-bot-service \
    --task-definition homuhomu-bot-task \
    --desired-count 1 \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[subnet-xxxxx],securityGroups=[sg-xxxxx],assignPublicIp=ENABLED}" \
    --region ap-northeast-1
```

**注意**: `subnet-xxxxx`と`sg-xxxxx`は実際のVPCのサブネットIDとセキュリティグループIDに置き換えてください。

### Step 6: デプロイ確認

```bash
# サービスの状態を確認
aws ecs describe-services \
    --cluster homuhomu-bot-cluster \
    --services homuhomu-bot-service \
    --region ap-northeast-1

# タスクの一覧を表示
aws ecs list-tasks \
    --cluster homuhomu-bot-cluster \
    --service-name homuhomu-bot-service \
    --region ap-northeast-1

# ログを確認（CloudWatch Logs）
aws logs tail /ecs/homuhomu-bot --follow --region ap-northeast-1
```

---

## 設定ファイル

### ecs-task-definition.json

以下の内容で`deploy/ecs-task-definition.json`を作成します：

```json
{
  "family": "homuhomu-bot-task",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "executionRoleArn": "arn:aws:iam::123456789012:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "homuhomu-bot",
      "image": "123456789012.dkr.ecr.ap-northeast-1.amazonaws.com/homuhomu-discordbot:latest",
      "essential": true,
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/homuhomu-bot",
          "awslogs-region": "ap-northeast-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "environment": [],
      "secrets": [
        {
          "name": "DISCORD_BOT_TOKEN",
          "valueFrom": "arn:aws:secretsmanager:ap-northeast-1:123456789012:secret:homuhomu-bot/discord-token-xxxxx"
        },
        {
          "name": "OSU_CLIENT_ID",
          "valueFrom": "arn:aws:secretsmanager:ap-northeast-1:123456789012:secret:homuhomu-bot/osu-client-id-xxxxx"
        },
        {
          "name": "OSU_CLIENT_SECRET",
          "valueFrom": "arn:aws:secretsmanager:ap-northeast-1:123456789012:secret:homuhomu-bot/osu-client-secret-xxxxx"
        },
        {
          "name": "TWITCH_CLIENT_ID",
          "valueFrom": "arn:aws:secretsmanager:ap-northeast-1:123456789012:secret:homuhomu-bot/twitch-client-id-xxxxx"
        },
        {
          "name": "TWITCH_CLIENT_SECRET",
          "valueFrom": "arn:aws:secretsmanager:ap-northeast-1:123456789012:secret:homuhomu-bot/twitch-client-secret-xxxxx"
        },
        {
          "name": "TWITCH_CHANNEL_NAME",
          "valueFrom": "arn:aws:secretsmanager:ap-northeast-1:123456789012:secret:homuhomu-bot/twitch-channel-name-xxxxx"
        },
        {
          "name": "TWITCH_NOTIFICATION_CHANNEL_ID",
          "valueFrom": "arn:aws:secretsmanager:ap-northeast-1:123456789012:secret:homuhomu-bot/twitch-notification-channel-id-xxxxx"
        },
        {
          "name": "NOTIFICATION_ROLE_ID",
          "valueFrom": "arn:aws:secretsmanager:ap-northeast-1:123456789012:secret:homuhomu-bot/notification-role-id-xxxxx"
        }
      ]
    }
  ]
}
```

**重要な設定項目:**

- `cpu`: "256" = 0.25 vCPU（最小）
- `memory`: "512" = 0.5 GB（最小）
- `executionRoleArn`: ECSタスク実行ロール（後述）
- `secrets`: AWS Secrets Managerから環境変数を取得

---

## 自動化スクリプト

### デプロイスクリプト

`deploy/deploy-to-ecs.sh`を作成します（後述のファイルを参照）。

使用方法:
```bash
chmod +x deploy/deploy-to-ecs.sh
./deploy/deploy-to-ecs.sh
```

### 更新方法

コードを更新した場合:
```bash
# 1. 新しいイメージをビルド＆プッシュ
./deploy/deploy-to-ecs.sh

# 2. サービスを更新（新しいタスク定義を使用）
aws ecs update-service \
    --cluster homuhomu-bot-cluster \
    --service homuhomu-bot-service \
    --force-new-deployment \
    --region ap-northeast-1
```

---

## IAMロールの設定

### Step 1: タスク実行ロールの作成

```bash
# 信頼ポリシーファイルを作成
cat > trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ecs-tasks.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# ロールを作成
aws iam create-role \
    --role-name ecsTaskExecutionRole \
    --assume-role-policy-document file://trust-policy.json

# AWSマネージドポリシーをアタッチ
aws iam attach-role-policy \
    --role-name ecsTaskExecutionRole \
    --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy
```

### Step 2: Secrets Managerへのアクセス権限を追加

```bash
# カスタムポリシーを作成
cat > secrets-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "arn:aws:secretsmanager:ap-northeast-1:123456789012:secret:homuhomu-bot/*"
    }
  ]
}
EOF

# ポリシーを作成してアタッチ
aws iam put-role-policy \
    --role-name ecsTaskExecutionRole \
    --policy-name SecretsManagerAccess \
    --policy-document file://secrets-policy.json
```

---

## AWS Secrets Managerでの環境変数管理

### シークレットの作成

```bash
# Discord Bot Token
aws secretsmanager create-secret \
    --name homuhomu-bot/discord-token \
    --secret-string "your_actual_discord_bot_token" \
    --region ap-northeast-1

# osu! Client ID
aws secretsmanager create-secret \
    --name homuhomu-bot/osu-client-id \
    --secret-string "your_osu_client_id" \
    --region ap-northeast-1

# osu! Client Secret
aws secretsmanager create-secret \
    --name homuhomu-bot/osu-client-secret \
    --secret-string "your_osu_client_secret" \
    --region ap-northeast-1

# 他の環境変数も同様に作成...
```

### シークレットの更新

```bash
aws secretsmanager update-secret \
    --secret-id homuhomu-bot/discord-token \
    --secret-string "new_token_value" \
    --region ap-northeast-1
```

---

## CloudWatch Logsの設定

### ロググループの作成

```bash
aws logs create-log-group \
    --log-group-name /ecs/homuhomu-bot \
    --region ap-northeast-1
```

### ログの確認

```bash
# リアルタイムでログを確認
aws logs tail /ecs/homuhomu-bot --follow --region ap-northeast-1

# 最新のログを表示
aws logs tail /ecs/homuhomu-bot --since 1h --region ap-northeast-1
```

---

## VPC・ネットワーク設定

### デフォルトVPCを使用する場合

```bash
# デフォルトVPCのIDを取得
aws ec2 describe-vpcs --filters "Name=isDefault,Values=true" --region ap-northeast-1

# サブネットの一覧を取得
aws ec2 describe-subnets --filters "Name=vpc-id,Values=vpc-xxxxx" --region ap-northeast-1

# セキュリティグループを作成（アウトバウンドのみ許可）
aws ec2 create-security-group \
    --group-name homuhomu-bot-sg \
    --description "Security group for Homuhomu Discord Bot" \
    --vpc-id vpc-xxxxx \
    --region ap-northeast-1

# アウトバウンドルールはデフォルトで全許可されているため、追加設定不要
```

---

## トラブルシューティング

### タスクが起動しない

**原因1: IAMロールの権限不足**
```bash
# タスク実行ロールにECRへのアクセス権限があるか確認
aws iam list-attached-role-policies --role-name ecsTaskExecutionRole
```

**原因2: イメージが見つからない**
```bash
# ECRにイメージが存在するか確認
aws ecr describe-images \
    --repository-name homuhomu-discordbot \
    --region ap-northeast-1
```

**原因3: ネットワーク設定の問題**
- パブリックサブネットを使用しているか確認
- `assignPublicIp=ENABLED`が設定されているか確認

### ログが表示されない

```bash
# CloudWatch Logsグループが存在するか確認
aws logs describe-log-groups \
    --log-group-name-prefix /ecs/homuhomu-bot \
    --region ap-northeast-1

# タスク実行ロールにCloudWatch Logsへの書き込み権限があるか確認
aws iam get-role-policy \
    --role-name ecsTaskExecutionRole \
    --policy-name AmazonECSTaskExecutionRolePolicy
```

### Botがオフラインになる

```bash
# タスクの状態を確認
aws ecs describe-tasks \
    --cluster homuhomu-bot-cluster \
    --tasks <task-arn> \
    --region ap-northeast-1

# サービスのイベントログを確認
aws ecs describe-services \
    --cluster homuhomu-bot-cluster \
    --services homuhomu-bot-service \
    --region ap-northeast-1
```

---

## コスト最適化

### 1. リザーブドインスタンス的な仕組み

FargateにはSavings Plansがあります：
- **Compute Savings Plans**: 最大17%割引

### 2. スポットインスタンス（Fargate Spot）

**70%のコスト削減**が可能：
```bash
aws ecs create-service \
    --cluster homuhomu-bot-cluster \
    --service-name homuhomu-bot-service \
    --task-definition homuhomu-bot-task \
    --desired-count 1 \
    --capacity-provider-strategy \
        capacityProvider=FARGATE_SPOT,weight=1 \
    --network-configuration "awsvpcConfiguration={subnets=[subnet-xxxxx],securityGroups=[sg-xxxxx],assignPublicIp=ENABLED}" \
    --region ap-northeast-1
```

**注意**: Spotは中断される可能性があるため、重要なBotには非推奨

### 3. スケジュール停止（夜間停止など）

```bash
# タスク数を0に設定（停止）
aws ecs update-service \
    --cluster homuhomu-bot-cluster \
    --service homuhomu-bot-service \
    --desired-count 0 \
    --region ap-northeast-1

# タスク数を1に設定（起動）
aws ecs update-service \
    --cluster homuhomu-bot-cluster \
    --service homuhomu-bot-service \
    --desired-count 1 \
    --region ap-northeast-1
```

EventBridgeで自動化可能。

---

## CI/CD統合

### GitHub Actionsでの自動デプロイ

`.github/workflows/deploy-ecs.yml`を作成（後述のファイルを参照）。

**必要なGitHub Secrets:**
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_REGION`
- `ECR_REPOSITORY`

---

## まとめ

### ECS (Fargate)のメリット

- ✅ サーバー管理不要
- ✅ AWSの高い信頼性
- ✅ CloudWatchとの統合
- ✅ スケーラビリティ

### デメリット

- ⚠️ 初期設定が複雑
- ⚠️ 月額$10程度のコスト
- ⚠️ AWS CLIの知識が必要

### 推奨度

- **AWSを使い慣れている**: ★★★★★
- **初心者**: ★★☆☆☆（Railwayの方が簡単）
- **コスト重視**: ★★★☆☆（Oracle Cloudの方が安い）

---

## 次のステップ

1. [自動化スクリプトを使用](#自動化スクリプト)
2. [CI/CDを設定](#cicd統合)
3. [CloudWatchアラームを設定](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/AlarmThatSendsEmail.html)

---

## 参考リンク

- [AWS ECS Documentation](https://docs.aws.amazon.com/ecs/)
- [Fargate Pricing](https://aws.amazon.com/fargate/pricing/)
- [AWS CLI Reference](https://docs.aws.amazon.com/cli/)

