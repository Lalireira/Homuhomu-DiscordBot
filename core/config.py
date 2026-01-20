#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""設定管理モジュール"""

import os
from dotenv import load_dotenv
from typing import Tuple, Optional, Dict, List

# 環境変数の読み込み
load_dotenv()


def get_osu_credentials() -> Tuple[Optional[str], Optional[str]]:
    """osu! API認証情報を取得"""
    return (
        os.getenv('OSU_CLIENT_ID'),
        os.getenv('OSU_CLIENT_SECRET')
    )


def get_discord_token() -> Optional[str]:
    """Discord Bot Tokenを取得"""
    return os.getenv('DISCORD_BOT_TOKEN')


def get_twitch_credentials() -> Tuple[Optional[str], Optional[str]]:
    """Twitch API認証情報を取得"""
    return (
        os.getenv('TWITCH_CLIENT_ID'),
        os.getenv('TWITCH_CLIENT_SECRET')
    )


def get_twitch_config() -> Dict:
    """Twitch通知設定を取得"""
    channel_id_str = os.getenv('TWITCH_DISCORD_CHANNEL_ID')
    channel_id = int(channel_id_str) if channel_id_str else None
    
    usernames_str = os.getenv('TWITCH_USERNAMES', '')
    usernames = [u.strip() for u in usernames_str.split(',') if u.strip()] if usernames_str else []
    
    check_interval_str = os.getenv('TWITCH_CHECK_INTERVAL', '60')
    check_interval = int(check_interval_str) if check_interval_str.isdigit() else 60
    
    return {
        'channel_id': channel_id,
        'usernames': usernames,
        'check_interval': check_interval
    }


def get_notification_role_id() -> Optional[int]:
    """通知ロールIDを取得"""
    role_id_str = os.getenv('NOTIFICATION_ROLE_ID')
    return int(role_id_str) if role_id_str else None


def get_notification_channel_id() -> Optional[int]:
    """通知管理チャンネルIDを取得"""
    channel_id_str = os.getenv('NOTIFICATION_CHANNEL_ID')
    return int(channel_id_str) if channel_id_str else None


def get_broadcast_allowed_users() -> Optional[List[int]]:
    """
    一斉メッセージ送信コマンドを実行できるユーザーIDのリストを取得
    
    Returns:
        許可されたユーザーIDのリスト
        - None: 環境変数が設定されていない（管理者権限でチェック）
        - []: 環境変数が空（誰も実行不可）
        - [user_id, ...]: 許可されたユーザーIDのリスト
    """
    # 環境変数が存在するかチェック
    if 'BROADCAST_ALLOWED_USER_IDS' not in os.environ:
        return None  # 環境変数が設定されていない
    
    user_ids_str = os.getenv('BROADCAST_ALLOWED_USER_IDS', '')
    if not user_ids_str or not user_ids_str.strip():
        return []  # 環境変数は設定されているが空
    
    user_ids = []
    for uid_str in user_ids_str.split(','):
        uid_str = uid_str.strip()
        if uid_str and uid_str.isdigit():
            user_ids.append(int(uid_str))
    
    return user_ids if user_ids else []