#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Twitch配信通知 タスクモジュール"""

import asyncio
import discord
from discord.ext import tasks
from typing import Optional
from core.twitch_api import TwitchAPIClient
from core.config import get_twitch_credentials, get_twitch_config, get_notification_role_id
from core.logger import get_logger
from .data import TwitchStreamMonitor
from .embeds import create_stream_notification_embed

logger = get_logger("twitch_notification")


class TwitchNotificationTask:
    """Twitch配信通知タスク"""
    
    def __init__(self, discord_client: discord.Client):
        self.discord_client = discord_client
        self.monitor: Optional[TwitchStreamMonitor] = None
        self.channel_id: Optional[int] = None
        self.check_interval: int = 60
        
    async def initialize(self) -> bool:
        """初期化"""
        client_id, client_secret = get_twitch_credentials()
        if not client_id or not client_secret:
            logger.error("Twitch API credentials are not configured.")
            return False
        
        config = get_twitch_config()
        self.channel_id = config['channel_id']
        usernames = config['usernames']
        self.check_interval = config['check_interval']
        
        if not self.channel_id:
            logger.error("TWITCH_DISCORD_CHANNEL_ID is not configured.")
            return False
        
        if not usernames:
            logger.warning("TWITCH_USERNAMES is not configured.")
            return False
        
        try:
            client = TwitchAPIClient(client_id, client_secret)
            self.monitor = TwitchStreamMonitor(client)
            
            if not self.monitor.initialize_user_ids(usernames):
                logger.error("Failed to initialize user IDs.")
                return False
            
            logger.info(f"Twitch通知を初期化しました: {len(usernames)}ユーザー監視")
            return True
        except Exception as e:
            logger.error(f"Twitch通知の初期化に失敗: {e}", exc_info=True)
            return False
    
    @tasks.loop(seconds=60)
    async def check_streams_task(self):
        """配信状況チェックタスク"""
        if not self.monitor:
            return
        
        try:
            new_streams = self.monitor.check_streams()
            
            for stream in new_streams:
                await self.send_notification(stream)
        except Exception as e:
            logger.error(f"配信チェックエラー: {e}", exc_info=True)
    
    async def send_notification(self, stream_data: dict):
        """Discord通知を送信"""
        max_retries = 3
        base_delay = 2
        
        for attempt in range(max_retries):
            try:
                channel = self.discord_client.get_channel(self.channel_id)
                if not channel:
                    logger.error(f"Discordチャンネルが見つかりません: {self.channel_id}")
                    logger.info("チャンネルIDを確認してください。また、Botがそのチャンネルにアクセスできる権限を持っているか確認してください。")
                    return
                
                # チャンネルへのアクセス権限を確認
                if not channel.permissions_for(channel.guild.me).send_messages:
                    logger.error(f"Botにチャンネル '{channel.name}' でメッセージ送信権限がありません")
                    logger.info("Discordサーバー設定で、Botに「Send Messages」権限を付与してください。")
                    return
                
                embed = create_stream_notification_embed(stream_data)
                
                # ロールメンション付きで通知送信
                role_id = get_notification_role_id()
                if role_id:
                    content = f"<@&{role_id}>"
                else:
                    content = "@everyone"
                
                await channel.send(content=content, embed=embed)
                logger.info(f"Discord通知送信: {stream_data['user_name']}")
                return
                
            except discord.Forbidden as e:
                logger.error(f"Discord通知エラー (権限不足): {e}")
                logger.info("以下の点を確認してください:")
                logger.info(f"  1. チャンネルID ({self.channel_id}) が正しいか")
                logger.info("  2. Botがそのチャンネルにアクセスできる権限を持っているか")
                logger.info("  3. Botに「Send Messages」「Embed Links」「Mention Everyone」権限があるか")
                logger.info("  4. Botがサーバーに正しく招待されているか")
                return
            except discord.HTTPException as e:
                if e.status == 503 or "503" in str(e):
                    # 503エラーの場合はリトライ
                    wait_time = base_delay * (2 ** attempt)
                    logger.warning(f"Discord通知エラー (試行 {attempt + 1}/{max_retries}): {e}")
                    if attempt < max_retries - 1:
                        logger.info(f"{wait_time}秒後にリトライします...")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        logger.error("Discord通知失敗: 最大リトライ回数に達しました")
                else:
                    logger.error(f"Discord通知エラー: {e}")
                    return
            except Exception as e:
                logger.error(f"Discord通知エラー: {e}", exc_info=True)
                return
    
    def start(self):
        """タスクを開始"""
        if self.monitor:
            self.check_streams_task.change_interval(seconds=self.check_interval)
            self.check_streams_task.start()
            logger.info(f"配信監視を開始しました (間隔: {self.check_interval}秒)")
    
    def stop(self):
        """タスクを停止"""
        if self.check_streams_task.is_running():
            self.check_streams_task.stop()
            logger.info("配信監視を停止しました")

