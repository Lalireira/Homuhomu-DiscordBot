#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一斉メッセージ送信 データ処理ロジック"""

import json
import asyncio
from pathlib import Path
from typing import List, Dict, Optional
import discord
from core.logger import get_logger

logger = get_logger("broadcast")


def get_template_dir() -> Path:
    """テンプレートディレクトリのパスを取得"""
    current_file = Path(__file__)
    return current_file.parent / "templates"


def load_template(template_name: str = "default") -> Optional[Dict]:
    """
    テンプレートファイルを読み込む
    
    Args:
        template_name: テンプレート名（拡張子なし）
    
    Returns:
        テンプレートデータ（辞書形式）、存在しない場合はNone
    """
    template_dir = get_template_dir()
    template_path = template_dir / f"{template_name}.json"
    
    if not template_path.exists():
        logger.warning(f"テンプレートが見つかりません: {template_name}")
        return None
    
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            template_data = json.load(f)
        logger.info(f"テンプレートを読み込みました: {template_name}")
        return template_data
    except json.JSONDecodeError as e:
        logger.error(f"テンプレートのJSON解析エラー: {template_name}, error={e}")
        return None
    except Exception as e:
        logger.error(f"テンプレート読み込みエラー: {template_name}, error={e}", exc_info=True)
        return None


def list_templates() -> List[str]:
    """利用可能なテンプレートのリストを取得"""
    template_dir = get_template_dir()
    if not template_dir.exists():
        return []
    
    templates = []
    for file_path in template_dir.glob("*.json"):
        templates.append(file_path.stem)
    
    return sorted(templates)


def format_message(template_data: Dict, variables: Optional[Dict] = None) -> str:
    """
    テンプレートデータからメッセージを生成
    
    Args:
        template_data: テンプレートデータ（辞書形式）
        variables: 変数辞書（テンプレート内の {variable} を置換）
    
    Returns:
        フォーマット済みメッセージ
    """
    if variables is None:
        variables = {}
    
    # テンプレートからメッセージを取得
    message = template_data.get("message", "")
    
    # 変数を置換
    try:
        formatted_message = message.format(**variables)
    except KeyError as e:
        logger.warning(f"テンプレート変数の不足: {e}")
        formatted_message = message
    
    return formatted_message


async def send_broadcast_message(
    bot: discord.Client,
    user_ids: List[int],
    message: str,
    max_retries: int = 3
) -> Dict:
    """
    指定されたユーザーに一斉メッセージを送信
    
    Args:
        bot: Discord Botクライアント
        user_ids: 送信先ユーザーIDのリスト
        message: 送信メッセージ
        max_retries: 最大リトライ回数
    
    Returns:
        結果統計と詳細情報（成功数、失敗数、スキップ数、各ユーザーの送信結果）
    """
    results = {
        "success": 0,
        "failed": 0,
        "skipped": 0,
        "success_users": [],  # [(user_id, username), ...]
        "failed_users": [],    # [(user_id, username or None), ...]
        "skipped_users": []   # [(user_id, username or None), ...]
    }
    
    for user_id in user_ids:
        try:
            user = await bot.fetch_user(user_id)
            username = f"{user.name}#{user.discriminator}" if user.discriminator != "0" else user.name
            
            # DMを送信
            await user.send(message)
            results["success"] += 1
            results["success_users"].append((user_id, username))
            logger.info(f"DM送信成功: user_id={user_id}, username={username}")
            
            # レート制限を避けるために少し待機（必要に応じて調整）
            await asyncio.sleep(1)
            
        except discord.Forbidden:
            # ユーザーがDMを無効化している場合
            try:
                user = await bot.fetch_user(user_id)
                username = f"{user.name}#{user.discriminator}" if user.discriminator != "0" else user.name
            except:
                username = None
            results["skipped"] += 1
            results["skipped_users"].append((user_id, username))
            logger.warning(f"DM送信スキップ（DM無効）: user_id={user_id}")
        except discord.NotFound:
            # ユーザーが見つからない場合
            results["failed"] += 1
            results["failed_users"].append((user_id, None))
            logger.warning(f"ユーザーが見つかりません: user_id={user_id}")
        except Exception as e:
            # その他のエラー（ユーザー情報取得を試みる）
            try:
                user = await bot.fetch_user(user_id)
                username = f"{user.name}#{user.discriminator}" if user.discriminator != "0" else user.name
            except:
                username = None
            results["failed"] += 1
            results["failed_users"].append((user_id, username))
            logger.error(f"DM送信エラー: user_id={user_id}, error={e}", exc_info=True)
    
    return results
