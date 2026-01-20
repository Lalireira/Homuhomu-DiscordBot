# osu! 2025 Wrapped

osu! API v2を使用して、2025年の1年間のプレイ統計を取得するツールです。

## 機能

- **ユーザーアイコン表示**: 指定したユーザーのアバターURLを取得
- **トップPP表示**: 2025年に取得したPPの上位10位までを表示
- **譜面情報**: カバー画像、アーティスト、タイトル、難易度、Star Rating、Modsを表示
- **プレイカウント**: ユーザーの総プレイカウントと2025年の正確なプレイカウントを表示
- **月別プレイカウント**: 2025年の月別プレイカウントデータを表示
- **Discord Bot対応**: スラッシュコマンドでDiscordから統計を取得可能
- **通知ロール管理**: ユーザーがボタンで通知のON/OFFを切り替え可能

## セットアップ

### 1. 必要なパッケージのインストール

```bash
pip install -r requirements.txt
```

### 2. osu! API認証情報の取得

1. [osu! アカウント設定ページ](https://osu.ppy.sh/home/account/edit#oauth) にアクセス
2. 「New OAuth Application」をクリック
3. アプリケーション名を入力（例: "osu 2025 Wrapped"）
4. Application Callback URLは `http://localhost` でOK
5. 「Client ID」と「Client Secret」をコピー

### 3. 環境変数の設定

`.env.example` をコピーして `.env` ファイルを作成し、取得した認証情報を設定します：

```bash
cp .env.example .env
```

`.env` ファイルを編集：

```
OSU_CLIENT_ID=あなたのClient ID
OSU_CLIENT_SECRET=あなたのClient Secret
```

## 使い方

### コマンドライン版

```bash
python main.py
```

実行すると、ユーザー名の入力を求められます：

```
osu! ユーザー名を入力してください: Reira
```

または、コマンドライン引数で指定：

```bash
python main.py Reira
```

### Discord Bot版

#### 1. Discord Botの作成

1. [Discord Developer Portal](https://discord.com/developers/applications) にアクセス
2. 「New Application」をクリックしてBotアプリケーションを作成
3. 左メニューの「Bot」を選択
4. 「Add Bot」をクリック
5. 「Token」の下の「Reset Token」または「Copy」をクリックしてBot Tokenをコピー
6. 「Privileged Gateway Intents」セクションで「MESSAGE CONTENT INTENT」を有効化（必要に応じて）

#### 2. Botをサーバーに招待

1. 左メニューの「OAuth2」→「URL Generator」を選択
2. 「Scopes」で「bot」と「applications.commands」にチェック
3. 「Bot Permissions」で必要最低限の権限を選択（例：Send Messages, Embed Links）
4. 生成されたURLにアクセスしてBotをサーバーに招待

#### 3. 環境変数の設定

`.env` ファイルにDiscord Bot Tokenを追加：

```
OSU_CLIENT_ID=あなたのClient ID
OSU_CLIENT_SECRET=あなたのClient Secret
DISCORD_BOT_TOKEN=あなたのDiscord Bot Token

# Twitch通知機能（オプション）
TWITCH_CLIENT_ID=あなたのTwitch Client ID
TWITCH_CLIENT_SECRET=あなたのTwitch Client Secret
TWITCH_DISCORD_CHANNEL_ID=123456789012345678
TWITCH_USERNAMES=username1,username2
TWITCH_CHECK_INTERVAL=60

# 通知ロール機能（オプション）
NOTIFICATION_ROLE_ID=123456789012345678
```

#### 4. Botの起動

```bash
python bot.py
```

Botが正常に起動すると、コンソールに以下のようなメッセージが表示されます：

```
Bot is ready! Logged in as YourBotName#1234
Synced 2 command(s)
```

#### 5. Discordでの使用

Discordサーバーで以下のコマンドを使用できます：

- `/wrapped <username>` - 詳細な2025年統計を表示（トップ10 PP、月別プレイカウントなど）
- `/wrapped_simple <username>` - 簡易版統計を表示（トップ3 PPのみ）
- `/notification` - 通知ロールのON/OFFを切り替え（NOTIFICATION_ROLE_ID設定時のみ）

例：
```
/wrapped Reira
/wrapped_simple Reira
/notification
```

#### 6. 通知ロール機能のセットアップ（オプション）

ユーザーが自分で通知のON/OFFを切り替えられる機能を使用する場合：

1. Discordサーバーで通知用のロールを作成（例：「お知らせ」）
2. ロールを右クリック→「ロールIDをコピー」
3. `.env` ファイルに `NOTIFICATION_ROLE_ID` を追加
4. Botに「ロールの管理」権限を付与
5. Botを再起動

これで、ユーザーが `/notification` コマンドを実行すると、ボタン付きのメッセージが表示され、
「🔔 通知ON」または「🔕 通知OFF」ボタンを押すことでロールの付与/削除が可能になります。

**必要な権限:**
- ロールの管理（Manage Roles）
- サーバーメンバーのインテント（Server Members Intent）

**注意:** Botのロールは、管理対象のロールよりも上位に配置する必要があります。

## 出力例

```
🎮 osu! 2025 Wrapped - Reira

================================================================================

📊 ユーザー情報を取得中...
✅ ユーザー: Reira (ID: 12345678)
🖼️  アイコン: https://a.ppy.sh/12345678

📈 ベストスコアを取得中...

🏆 2025年に取得したPP - トップ10
================================================================================

1. 450.25pp
   🎵 Camellia - GHOST
   📊 [Extra] - 7.89⭐ +HDDT
   🖼️  https://assets.ppy.sh/beatmaps/...
   📅 2025-06-15

2. 438.50pp
   🎵 xi - FREEDOM DiVE
   📊 [FOUR DIMENSIONS] - 8.12⭐ +HR
   🖼️  https://assets.ppy.sh/beatmaps/...
   📅 2025-05-20

...

📊 統計情報
================================================================================
総プレイカウント: 50,000
2025年のベストスコア数: 45
2025年の上位PPスコア数（表示）: 10

================================================================================
✨ 完了！
```

## 注意事項

- **月別プレイカウント**: osu! API v2の`monthly_playcounts`を使用して2025年の正確なプレイカウントを取得しています
- **ベストスコア**: ベストスコア（トップ100）の中から2025年のスコアをフィルタリングしています
- **APIレート制限**: osu! APIのレート制限にご注意ください
- **Discord Bot**: Botが複数のサーバーで使用される場合、APIレート制限に特に注意が必要です

## 技術仕様

- **言語**: Python 3.8+
- **API**: osu! API v2
- **認証**: OAuth2 Client Credentials Grant
- **Discord Bot**: discord.py 2.3.2+

## プロジェクト構造と実装方針

このBotは、今後様々な機能を追加していく予定です。機能ごとにディレクトリを分けて管理し、コードの可読性と保守性を向上させます。

詳細な構造と実装方針については、[PROJECT_STRUCTURE.md](./PROJECT_STRUCTURE.md) を参照してください。

### 主な方針

- **機能ごとのモジュール化**: 各機能は`features/`配下の独立したディレクトリに配置
- **コア機能の分離**: 共通機能（APIクライアント、ユーティリティなど）は`core/`に配置
- **責務の分離**: コマンド、Embed作成、データ処理を別ファイルに分離
- **拡張性**: 新しい機能を追加しやすい構造

### 新しい機能を追加する場合

1. `features/[機能名]/`ディレクトリを作成
2. `commands.py`, `embeds.py`, `data.py`などのファイルを作成
3. `bot.py`でコマンドを登録

詳細は [PROJECT_STRUCTURE.md](./PROJECT_STRUCTURE.md) を参照してください。

## クラウドデプロイ

このBotを24時間365日稼働させるには、クラウドサービスにデプロイすることをおすすめします。

### 📚 デプロイガイド

- **[クイックスタート（5分でデプロイ）](./QUICK_START_DEPLOY.md)** - Railway使用
- **[詳細なデプロイガイド](./DEPLOYMENT_GUIDE.md)** - Railway、Oracle Cloud、AWS、Renderの比較

### 🚀 推奨デプロイ方法

| サービス | 月額コスト | 難易度 | 推奨度 |
|---------|----------|-------|-------|
| **Railway** | $5無料枠内 | ★☆☆☆☆ | ★★★★★ |
| **Oracle Cloud** | **完全無料** | ★★★☆☆ | ★★★★★ |
| **AWS EC2** | 12ヶ月無料 | ★★★☆☆ | ★★★★☆ |

詳細は [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) を参照してください。

## Docker対応

このプロジェクトはDocker/Docker Composeに完全対応しています。

### ローカルでの起動

```bash
# .envファイルを作成（env.exampleを参考に）
cp env.example .env
nano .env

# Docker Composeで起動
docker-compose up -d

# ログ確認
docker-compose logs -f

# 停止
docker-compose down
```

### 自動セットアップスクリプト

Oracle CloudやAWS EC2にデプロイする場合、自動セットアップスクリプトが用意されています：

```bash
# Oracle Cloud
bash deploy/setup-oracle-cloud.sh

# AWS EC2
bash deploy/setup-aws-ec2.sh
```

## ライセンス

MIT License

## 参考リンク

- [osu! API v2 ドキュメント](https://osu.ppy.sh/docs/index.html)
- [osu! 公式サイト](https://osu.ppy.sh/)
- [Discord.py ドキュメント](https://discordpy.readthedocs.io/)
- [Railway](https://railway.app/)
- [Oracle Cloud Free Tier](https://www.oracle.com/cloud/free/)

