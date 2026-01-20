#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Discord Bot メインエントリーポイント"""

import logging
import discord
from discord import app_commands
from discord.ext import commands
from core.config import get_discord_token, get_notification_role_id
from core.logger import setup_logger
from features.wrapped.commands import wrapped_command_handler, wrapped_simple_command_handler
from features.twitch_notification.tasks import TwitchNotificationTask
from features.notification_role.commands import notification_role_command_handler, NotificationRoleView
from features.broadcast.commands import broadcast_command_handler, list_templates_command_handler
from features.config_reload.commands import config_reload_command_handler

# メインロガーのセットアップ
logger = setup_logger("bot")


# 再接続ログをINFOレベルに降格するフィルタ
class ReconnectLogFilter(logging.Filter):
    """WebSocket再接続ログをERRORからINFOレベルに変更するフィルタ"""
    
    def filter(self, record):
        # 再接続メッセージの場合、ログレベルをINFOに変更
        if record.levelno == logging.ERROR and "reconnect" in record.getMessage().lower():
            record.levelno = logging.INFO
            record.levelname = "INFO"
        return True


# discord.pyのロガー設定
discord_logger = logging.getLogger("discord")
discord_logger.setLevel(logging.INFO)

discord_client_logger = logging.getLogger("discord.client")
discord_client_logger.setLevel(logging.INFO)
discord_client_logger.addFilter(ReconnectLogFilter())  # 再接続ログをINFOレベルに降格

# Bot設定
intents = discord.Intents.none()
intents.guilds = True  # サーバー情報が必要
intents.members = True  # ロール管理に必要
bot = commands.Bot(command_prefix='!', intents=intents)

# Twitch通知タスク
twitch_task: TwitchNotificationTask = None


# スラッシュコマンドを同期するために必要
@bot.event
async def on_ready():
    logger.info(f'is ready! Logged in as {bot.user}')
    
    # 永続的なViewを登録（Bot再起動時もボタンが機能するように）
    role_id = get_notification_role_id()
    if role_id:
        bot.add_view(NotificationRoleView(role_id))
        logger.info(f"通知ロールViewを登録しました: role_id={role_id}")
    else:
        logger.warning("NOTIFICATION_ROLE_IDが設定されていないため、通知ロール機能は無効です")
    
    try:
        synced = await bot.tree.sync()
        logger.info(f'Synced {len(synced)} command(s)')
        # 同期されたコマンド名をログに出力
        for cmd in synced:
            logger.info(f'  - /{cmd.name}')
    except Exception as e:
        logger.error(f'Failed to sync commands: {e}', exc_info=True)
    
    # Twitch通知タスクの初期化と開始
    global twitch_task
    twitch_task = TwitchNotificationTask(bot)
    if await twitch_task.initialize():
        twitch_task.start()
    else:
        logger.warning("Twitch通知機能は無効化されています")


@bot.tree.command(name="wrapped", description="osu! 2025年のプレイ統計を表示します")
@app_commands.describe(username="osu! ユーザー名")
async def wrapped_command(interaction: discord.Interaction, username: str):
    """osu! 2025 Wrappedコマンド"""
    await wrapped_command_handler(interaction, username)


@bot.tree.command(name="wrapped_simple", description="Display simplified osu! 2025 statistics")
@app_commands.describe(username="osu! username")
async def wrapped_simple_command(interaction: discord.Interaction, username: str):
    """簡易版osu! 2025 Wrappedコマンド"""
    await wrapped_simple_command_handler(interaction, username)


@bot.tree.command(name="notification", description="通知のON/OFFを設定します")
async def notification_command(interaction: discord.Interaction):
    """通知ロール管理コマンド"""
    await notification_role_command_handler(interaction)


@bot.tree.command(name="broadcast", description="指定したユーザーに一斉メッセージを送信します（管理者のみ）")
@app_commands.describe(
    user_ids="送信先ユーザーID（カンマ区切り、例: 123456789,987654321）",
    template_name="使用するテンプレート名（デフォルト: default）",
    variables="変数（カンマ区切り、例: username:John,date:2024-01-01）"
)
async def broadcast_command(
    interaction: discord.Interaction,
    user_ids: str,
    template_name: str = "default",
    variables: str = None
):
    """一斉メッセージ送信コマンド"""
    await broadcast_command_handler(interaction, user_ids, template_name, variables)


@bot.tree.command(name="broadcast_templates", description="利用可能なテンプレート一覧を表示します")
async def broadcast_templates_command(interaction: discord.Interaction):
    """テンプレート一覧表示コマンド"""
    await list_templates_command_handler(interaction)


@bot.tree.command(name="config_reload", description="環境変数を再読み込みします（管理者のみ）")
async def config_reload_command(interaction: discord.Interaction):
    """設定リロードコマンド"""
    await config_reload_command_handler(interaction)


# Botを起動
if __name__ == "__main__":
    token = get_discord_token()
    if not token:
        logger.error("DISCORD_BOT_TOKEN is not set in .env file")
        exit(1)
    
    try:
        bot.run(token)
    except KeyboardInterrupt:
        logger.info("Botを停止しています...")
        if twitch_task:
            twitch_task.stop()
    except Exception as e:
        logger.error(f"Bot実行エラー: {e}", exc_info=True)
