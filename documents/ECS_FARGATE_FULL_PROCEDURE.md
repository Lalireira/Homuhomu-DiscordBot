# Discord Bot を AWS ECS(Fargate) で常時稼働させるまでの全手順まとめ
## （躓きポイントとリカバリ手順付き）

---

## 0. 概要

本ドキュメントは、Python 製 Discord Bot **Homuhomu-DiscordBot** を **AWS ECS(Fargate)** 上で常時稼働させるまでに行った

- 構築の全手順
- 実際に発生したエラー（躓きポイント）
- それぞれの原因とリカバリ方法

を **再現可能な形で完全にまとめたもの** です。

---

## 1. 全体アーキテクチャ（完成形）

```text
GitHub Repository
   └─ Homuhomu-DiscordBot (Python)
          ↓
Docker build
          ↓
Amazon ECR (Docker Image)
          ↓
Amazon ECS (Fargate Service)
          ↓
Discord API
```

---

## 2. フェーズ1：AWS 基盤準備

### 2.1 リージョン選定

**使用リージョン：** `ap-northeast-1`（東京）

ECS / ECR / Secrets Manager / IAM をすべて同一リージョンで統一する。

### 2.2 IAM ロール作成

**作成したロール**

- `ecsTaskExecutionRole`
- GitHub Actions 用 OIDC ロール（将来用）

**ecsTaskExecutionRole の信頼ポリシー（正）**

```json
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
```

#### ❌ 躓き①：ECS クラスター作成失敗

**エラー**

```text
Unable to assume the service linked role
```

**原因**

- CloudFormation で作成途中のスタックが残っていた

**リカバリ**

1. **CloudFormation コンソール** を開く
2. 失敗した ECS クラスター用スタックを**削除**
3. **再度 ECS クラスター作成** を実行

---

## 3. フェーズ2：Docker & ECR

### 3.1 ECR リポジトリ作成

- **リポジトリ名：** `homuhomu-discord-bot`
- **種別：** Private Repository

### 3.2 CloudShell セットアップ

```bash
git clone https://github.com/Lalireira/Homuhomu-DiscordBot.git
cd Homuhomu-DiscordBot
```

### 3.3 Dockerfile 作成

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "bot.py"]
```

### 3.4 Docker build & push

```bash
docker build -t homuhomu-discord-bot .
docker tag homuhomu-discord-bot:latest \
  587821825996.dkr.ecr.ap-northeast-1.amazonaws.com/homuhomu-discord-bot:latest
docker push 587821825996.dkr.ecr.ap-northeast-1.amazonaws.com/homuhomu-discord-bot:latest
```

#### ❌ 躓き②：Docker build 失敗

**原因**

- リポジトリを `clone` していなかった
- `Dockerfile` が存在しなかった

**リカバリ**

- 正しいディレクトリで `Dockerfile` を作成する  
- `git clone` 後、プロジェクトルートで `docker build` を実行する

#### ❌ 躓き③：CannotPullContainerError

**エラー**

```text
image:latest not found
```

**原因**

- ECR に image が push されていなかった

**リカバリ**

- `docker tag` と `docker push` を実施する

---

## 4. フェーズ3：ECS Task Definition

### 4.1 Task Definition 設定

| 項目     | 値                 |
|----------|--------------------|
| 起動タイプ | Fargate            |
| CPU      | 0.25 vCPU          |
| メモリ   | 512MB 〜 2GB       |
| OS       | Linux              |

### 4.2 コンテナ設定

- **イメージ：** ECR の `latest`
- **ポート公開：** なし
- **コマンド：** Dockerfile の `CMD` を使用
- **ログ：** CloudWatch Logs（`awslogs`）

#### ❌ 躓き④：CPU / メモリ不整合

**原因**

- タスク CPU とコンテナ CPU の合計が一致していなかった

**リカバリ**

- **タスク CPU** = `0.25 vCPU`
- **コンテナ CPU** = `256`

---

## 5. フェーズ4：Secrets Manager & 環境変数

### 5.1 Secrets Manager 作成（上級構成）

**Secret 名**

```text
discord/homuhomu/bot-token
```

**値（JSON）**

```json
{
  "DISCORD_BOT_TOKEN": "xxxxxxxxxxxxxxxx"
}
```

### 5.2 ECS Task Definition（Secrets）

環境変数で Secrets を参照する場合の形式：

```text
arn:aws:secretsmanager:ap-northeast-1:587821825996:secret:discord/homuhomu/bot-token-XXXXXX:DISCORD_BOT_TOKEN::
```

#### ❌ 躓き⑤：.env 前提コード

**エラー**

```text
DISCORD_BOT_TOKEN is not set in .env file
```

**原因**

- ECS には `.env` ファイルは存在しない

**リカバリ**

- **Secrets Manager** と **ECS Secrets** で環境変数を注入する  
- アプリ側は `os.environ["DISCORD_BOT_TOKEN"]` など、環境変数参照に統一する

#### ❌ 躓き⑥：Improper token has been passed

**原因**

- Bot Token ではなく **Client Secret** を使用していた
- **ARN をそのまま**環境変数に設定していた（キー指定なし）
- JSON キー指定（`:KEY::`）の漏れ

**リカバリ**

- 正しい **Bot Token** を Discord Developer Portal で再生成
- Secrets の ARN に **`:DISCORD_BOT_TOKEN::`** を付与する

---

## 6. フェーズ5：IAM 権限（最大の鬼門）

#### ❌ 躓き⑦：Secrets 取得失敗

**エラー**

```text
AccessDeniedException: secretsmanager:GetSecretValue
```

**原因**

- `ecsTaskExecutionRole` に Secrets Manager への権限が不足していた

### 6.1 正しい権限追加

**Execution Role** に以下のインラインポリシー（またはマネージドポリシー）を追加する：

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "secretsmanager:GetSecretValue",
      "Resource": "arn:aws:secretsmanager:ap-northeast-1:587821825996:secret:discord/homuhomu/bot-token-XXXXXX"
    }
  ]
}
```

> **注意：** `Resource` の `discord/homuhomu/bot-token-XXXXXX` の `XXXXXX` は、Secrets Manager で作成されたサフィックス。コンソールの ARN をそのままコピーすること。

#### ❌ 勘違いしやすい点

| 誤解               | 正解                      |
|--------------------|---------------------------|
| 信頼ポリシーを直す | ❌ 対象外                 |
| Task Role に付ける | ❌ 間違い                 |
| **Execution Role** に付与 | ✅ **ここに付与** |

---

## 7. フェーズ6：ECS Service 起動

### 7.1 Service 作成

- **Desired tasks：** `1`
- **Public IP：** 有効
- **Load Balancer：** なし

### 7.2 強制新規デプロイ

タスク定義を更新しただけではコンテナが再起動しない場合、  
**「新しいデプロイの強制」** でサービスを再デプロイする。

---

## 8. 成功時の状態

**CloudWatch Logs**

```text
INFO discord.client: logging in using static token
INFO discord.gateway: Shard ID None has connected
```

**ECS**

- タスク：`RUNNING`

**Discord**

- Bot がオンライン 🟢

---

## 9. まとめ（重要ポイント）

| 項目 | 内容 |
|------|------|
| ECS Secrets | **Execution Role** に `secretsmanager:GetSecretValue` を付与 |
| ARN の `-XXXXXX` | **省略不可**（Secrets Manager のサフィックス） |
| `:KEY::` 指定 | **必須**（例：`:DISCORD_BOT_TOKEN::`） |
| `.env` | ECS では使えない → Secrets Manager + 環境変数 |
| 失敗時の確認 | **CloudWatch Logs** を必ず確認する |

---

*本ドキュメントは、Homuhomu-DiscordBot を AWS ECS (Fargate) で運用する際の再現手順およびトラブルシューティング用として作成しました。*
