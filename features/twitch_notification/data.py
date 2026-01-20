#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Twitch配信通知 データ取得・処理モジュール"""

from typing import Dict, List, Set
from core.twitch_api import TwitchAPIClient
from core.logger import get_logger

logger = get_logger("twitch_notification")


class TwitchStreamMonitor:
    """Twitch配信監視クラス"""
    
    def __init__(self, client: TwitchAPIClient):
        self.client = client
        self.user_ids: Dict[str, str] = {}  # ユーザー名 -> ユーザーIDマッピング
        self.currently_live: Set[str] = set()  # 現在配信中のユーザー名
    
    def initialize_user_ids(self, usernames: List[str]) -> bool:
        """ユーザーIDを初期化"""
        try:
            self.user_ids = self.client.get_user_ids(usernames)
            logger.info(f"ユーザーID取得完了: {len(self.user_ids)}人")
            return len(self.user_ids) > 0
        except Exception as e:
            logger.error(f"ユーザーID取得エラー: {e}", exc_info=True)
            return False
    
    def check_streams(self) -> List[Dict]:
        """配信状況をチェックして新規配信を返す"""
        if not self.user_ids:
            return []
        
        try:
            streams = self.client.get_streams(list(self.user_ids.values()))
            current_live = set()
            new_streams = []
            
            for stream in streams:
                username = stream['user_login']
                current_live.add(username)
                
                # 新規配信開始の場合
                if username not in self.currently_live:
                    new_streams.append(stream)
            
            # 配信終了したユーザーをセットから削除
            self.currently_live = current_live
            
            return new_streams
        except Exception as e:
            logger.error(f"配信状況チェックエラー: {e}", exc_info=True)
            # トークンが無効な場合は再認証
            if "401" in str(e) or "Unauthorized" in str(e):
                try:
                    self.client._authenticate()
                    logger.info("Twitchアクセストークンを再取得しました")
                except Exception as auth_error:
                    logger.error(f"Twitchアクセストークンの再取得に失敗: {auth_error}")
            return []

