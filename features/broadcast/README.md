# 一斉メッセージ送信機能

指定したユーザーに対して一斉にDM（ダイレクトメッセージ）を送信する機能です。

## 機能概要

- 複数のユーザーIDを指定して一斉にメッセージを送信
- メッセージフォーマットを外部テンプレートファイル（JSON）で定義可能
- テンプレート内で変数を使用可能（例: `{username}`, `{date}`）

## コマンド

### `/broadcast`

指定したユーザーに一斉メッセージを送信します。

**パラメータ:**
- `user_ids` (必須): 送信先ユーザーID（カンマ区切り、例: `123456789,987654321`）
- `template_name` (オプション): 使用するテンプレート名（デフォルト: `default`）
- `variables` (オプション): テンプレート変数（カンマ区切り、例: `username:John,date:2024-01-01`）

**使用例:**
```
/broadcast user_ids:123456789,987654321 template_name:default
/broadcast user_ids:123456789,987654321 template_name:example variables:username:John,date:2024-01-01
```

**注意事項:**
- このコマンドは管理者のみ実行できます
- レート制限を避けるため、送信間隔に1秒の待機時間があります

### `/broadcast_templates`

利用可能なテンプレート一覧を表示します。

## テンプレートファイル

テンプレートファイルは `features/broadcast/templates/` ディレクトリに配置します。

### テンプレートファイル形式

JSONファイルとして保存します（拡張子: `.json`）

```json
{
  "name": "テンプレート名",
  "description": "テンプレートの説明",
  "message": "メッセージ内容\n\n{username}さん、こんにちは！\n本日は{date}です。"
}
```

### 変数の使用

テンプレート内の `{変数名}` は、`variables` パラメータで指定した値に置換されます。

**例:**

テンプレート (`example.json`):
```json
{
  "name": "サンプルテンプレート",
  "description": "変数を使用したサンプルテンプレート",
  "message": "こんにちは、{username}さん！\n\n本日は{date}です。\n\n{content}\n\nよろしくお願いいたします。"
}
```

コマンド:
```
/broadcast user_ids:123456789 template_name:example variables:username:John,date:2024-01-01,content:重要な通知です
```

送信されるメッセージ:
```
こんにちは、Johnさん！

本日は2024-01-01です。

重要な通知です

よろしくお願いいたします。
```

### デフォルトテンプレート

`default.json` がデフォルトで使用されるテンプレートです。

## テンプレートの追加方法

1. `features/broadcast/templates/` ディレクトリに新しいJSONファイルを作成
2. ファイル名がテンプレート名になります（例: `announcement.json` → テンプレート名: `announcement`）
3. JSONファイルに `name`, `description`, `message` を記述
4. `/broadcast_templates` コマンドで確認

## エラーハンドリング

送信時に以下のエラーが発生する可能性があります：

- **DM無効**: ユーザーがDMを受け取れない設定になっている場合 → スキップ
- **ユーザー未找到**: 指定されたユーザーIDが存在しない場合 → 失敗
- **その他のエラー**: ネットワークエラーなど → 失敗

送信結果は統計として表示されます（成功数、スキップ数、失敗数）。
