#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Twitch配信通知 Embed作成モジュール"""

from datetime import datetime, timezone, timedelta
import discord


def create_stream_notification_embed(stream_data: dict) -> discord.Embed:
    """Twitch配信通知のEmbedを作成"""
    embed = discord.Embed(
        title="🔴 配信開始！",
        description=f"**{stream_data['user_name']}** が配信を開始しました！",
        color=0x9146FF,  # Twitchの紫色
        url=f"https://www.twitch.tv/{stream_data['user_login']}"
    )
    
    embed.add_field(
        name="配信タイトル",
        value=stream_data.get('title', 'タイトルなし'),
        inline=False
    )
    
    embed.add_field(
        name="ゲーム/カテゴリ",
        value=stream_data.get('game_name', '不明'),
        inline=True
    )
    
    embed.add_field(
        name="視聴者数",
        value=f"{stream_data.get('viewer_count', 0)}人",
        inline=True
    )
    
    # サムネイル設定
    thumbnail_url = stream_data.get('thumbnail_url', '')
    if thumbnail_url:
        # サムネイルサイズを指定
        thumbnail_url = thumbnail_url.replace('{width}', '320').replace('{height}', '180')
        embed.set_image(url=thumbnail_url)
    
    embed.set_footer(text="Twitch配信通知BOT")
    embed.timestamp = datetime.now(timezone(timedelta(hours=9)))
    
    return embed

