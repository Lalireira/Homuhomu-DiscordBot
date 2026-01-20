# プロジェクト構造と実装方針

## ディレクトリ構造

今後、機能ごとにディレクトリを分けて管理します。推奨される構造は以下の通りです：

```
osu2025-wrapped/
├── bot.py                    # Discord Botのメインエントリーポイント
├── main.py                   # コマンドライン版のエントリーポイント（後方互換性のため残存）
├── requirements.txt          # Python依存パッケージ
├── .env                      # 環境変数（gitignore対象）
├── .env.example              # 環境変数のサンプル（.gitignore対象）
├── README.md                 # プロジェクトの概要とセットアップ
├── documents/                # ドキュメントディレクトリ
│   ├── README.md            # 詳細なREADME
│   └── PROJECT_STRUCTURE.md # このファイル（プロジェクト構造と実装方針）
│
├── core/                     # コア機能・共通ライブラリ
│   ├── __init__.py
│   ├── osu_api.py           # osu! APIクライアント（main.pyから移行予定）
│   ├── utils.py             # ユーティリティ関数（フォーマット、計算など）
│   └── config.py            # 設定管理
│
├── features/                 # 機能ごとのディレクトリ
│   ├── __init__.py
│   │
│   ├── wrapped/              # osu! 2025 Wrapped機能
│   │   ├── __init__.py
│   │   ├── commands.py      # スラッシュコマンド定義
│   │   ├── embeds.py        # Embed作成ロジック
│   │   └── data.py          # データ取得・処理ロジック
│   │
│   └── [将来の機能]/         # 例: beatmap_search, user_stats, etc.
│       ├── __init__.py
│       ├── commands.py
│       ├── embeds.py
│       └── data.py
│
└── tests/                    # テストコード（将来追加予定）
    ├── __init__.py
    ├── test_core/
    └── test_features/
```

## 実装方針

### 1. モジュール化の原則

- **機能ごとに独立したモジュール**: 各機能は`features/`配下の独自ディレクトリに配置
- **コア機能の分離**: 共通で使用される機能（APIクライアント、ユーティリティなど）は`core/`に配置
- **依存関係の明確化**: 機能間の依存は最小限にし、`core/`を通じて共通機能を使用

### 2. コード構成パターン

各機能ディレクトリは以下のファイル構成を推奨します：

```
features/[機能名]/
├── __init__.py           # モジュールの公開API
├── commands.py           # Discordスラッシュコマンド定義
├── embeds.py            # Discord Embed作成ロジック
├── data.py              # データ取得・処理ロジック
└── models.py            # データモデル（必要に応じて）
```

**責務の分離**:
- `commands.py`: Discordコマンドのインターフェース、エラーハンドリング、レスポンス
- `embeds.py`: Discord Embedのフォーマットとスタイリング
- `data.py`: API呼び出し、データ処理、ビジネスロジック

### 3. 命名規則

- **ディレクトリ名**: `snake_case`（例: `wrapped`, `beatmap_search`）
- **ファイル名**: `snake_case`（例: `commands.py`, `osu_api.py`）
- **クラス名**: `PascalCase`（例: `OsuAPIClient`, `WrappedCommand`）
- **関数名**: `snake_case`（例: `get_user_stats`, `create_wrapped_embed`）
- **定数**: `UPPER_SNAKE_CASE`（例: `BASE_URL`, `MAX_RESULTS`）

### 4. コマンド追加の手順

新しい機能（コマンド）を追加する場合：

1. **ディレクトリ作成**: `features/[機能名]/`を作成
2. **必要ファイルの作成**: `__init__.py`, `commands.py`, `embeds.py`, `data.py`
3. **コマンド実装**: `commands.py`にスラッシュコマンドを定義
4. **Botへの登録**: `bot.py`でコマンドをインポートして登録

**例: 新しい機能「beatmap_search」を追加する場合**

```python
# features/beatmap_search/commands.py
from discord import app_commands
from discord.ext import commands
from .data import search_beatmap
from .embeds import create_beatmap_embed

@commands.hybrid_command(name="beatmap")
@app_commands.describe(query="検索クエリ")
async def beatmap_command(ctx: commands.Context, query: str):
    """譜面を検索する"""
    await ctx.defer()
    
    try:
        beatmap_data = await search_beatmap(query)
        embed = create_beatmap_embed(beatmap_data)
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ エラー: {str(e)}")

# bot.py
from features.beatmap_search.commands import beatmap_command
bot.add_command(beatmap_command)
```

### 5. 共通機能の使用

`core/`配下の機能は、すべての機能から使用できます：

```python
# features/wrapped/data.py
from core.osu_api import OsuAPIClient
from core.config import get_osu_credentials

def get_user_stats(username: str):
    client_id, client_secret = get_osu_credentials()
    client = OsuAPIClient(client_id, client_secret)
    # ...
```

### 6. 設定管理

環境変数や設定は`core/config.py`で一元管理：

```python
# core/config.py
import os
from dotenv import load_dotenv

load_dotenv()

def get_osu_credentials():
    return (
        os.getenv('OSU_CLIENT_ID'),
        os.getenv('OSU_CLIENT_SECRET')
    )

def get_discord_token():
    return os.getenv('DISCORD_BOT_TOKEN')
```

### 7. エラーハンドリング

- **APIエラー**: `core/osu_api.py`で統一的なエラーハンドリング
- **コマンドエラー**: 各`commands.py`でユーザーフレンドリーなエラーメッセージを返す
- **ログ出力**: エラーは必ずログに記録（将来、ロギングライブラリを導入予定）

### 8. 非同期処理

- **API呼び出し**: 長時間かかる可能性があるため、`asyncio`を使用して非同期実行
- **コマンド処理**: Discord Botのコマンドは全て`async/await`を使用
- **デファー**: レスポンスに時間がかかる場合は`ctx.defer()`または`interaction.response.defer()`を使用

### 9. 型ヒント

可能な限り型ヒントを付与してコードの可読性を向上：

```python
from typing import Optional, Dict, List

def get_user_stats(username: str) -> Optional[Dict]:
    """ユーザー統計を取得"""
    # ...
```

### 10. ドキュメンテーション

- **docstring**: すべての関数・クラスにdocstringを記述
- **コメント**: 複雑なロジックには説明コメントを追加
- **README**: 各機能ディレクトリに必要に応じて`README.md`を追加

## リファクタリング完了 ✅

既存のコードを上記の構造に移行しました：

### Phase 1: コア機能の分離 ✅
- [x] `main.py`の`OsuAPIClient`を`core/osu_api.py`に移動
- [x] ユーティリティ関数（`format_mods`, `calculate_modded_star_rating`, `get_modded_star_rating_from_api`）を`core/utils.py`に移動
- [x] 設定管理を`core/config.py`に集約

### Phase 2: Wrapped機能の分離 ✅
- [x] `features/wrapped/`ディレクトリを作成
- [x] `bot.py`の`create_wrapped_embed`を`features/wrapped/embeds.py`に移動
- [x] `main.py`の`get_2025_stats_data`、`filter_2025_scores`、`calculate_2025_playcount`、`get_monthly_2025_data`を`features/wrapped/data.py`に移動
- [x] コマンドハンドラーを`features/wrapped/commands.py`に移動

### Phase 3: Botメインファイルの簡素化 ✅
- [x] `bot.py`をエントリーポイントのみに簡素化
- [x] コマンド定義を`features/wrapped/commands.py`からインポートして使用

**注意**: 
- `main.py`は**コマンドライン版のエントリーポイント**として機能しており、後方互換性のために残存しています
- `main.py`内の関数やクラスは全て`core/`と`features/`に移動済みで、`main.py`はそれらをインポートして使用しています
- `bot.py`（Discord Bot版）からは`main.py`は使用されておらず、完全に独立しています
- コマンドライン版を使用する場合は`python main.py`で実行できます

## 将来の拡張例

以下のような機能追加が考えられます：

- **`features/beatmap_search/`**: 譜面検索機能
- **`features/user_compare/`**: ユーザー比較機能
- **`features/recent_plays/`**: 最近のプレイ表示
- **`features/rankings/`**: ランキング表示
- **`features/achievements/`**: 実績表示

各機能は独立して開発・テストが可能な構造になっています。

