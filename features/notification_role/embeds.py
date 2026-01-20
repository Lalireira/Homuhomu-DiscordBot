#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""通知ロール管理Embed作成モジュール"""

import discord


def create_notification_role_embed() -> discord.Embed:
    """通知ロール選択用のEmbedを作成"""
    embed = discord.Embed(
        title="🔔 配信通知設定",
        description="下のボタンを押して、通知のON/OFFを切り替えてください。",
        color=0x5865F2  # Discord Blurple
    )
    
    embed.add_field(
        name="通知ON",
        value="配信通知ロールが付与され、配信通知が届くようになります。",
        inline=False
    )
    
    embed.add_field(
        name="通知OFF",
        value="配信通知ロールが削除され、配信通知を受け取らなくなります。",
        inline=False
    )
    
    embed.set_footer(text="ボタンは何度でも押し直すことができます。")
    
    return embed


def create_success_embed(enabled: bool) -> discord.Embed:
    """成功メッセージ用のEmbedを作成"""
    if enabled:
        embed = discord.Embed(
            title="✅ 通知をONにしました",
            description="配信通知ロールが付与されました。",
            color=0x57F287  # Discord Green
        )
    else:
        embed = discord.Embed(
            title="✅ 通知をOFFにしました",
            description="配信通知ロールが削除されました。",
            color=0xED4245  # Discord Red
        )
    
    return embed


def create_error_embed(error_message: str) -> discord.Embed:
    """エラーメッセージ用のEmbedを作成"""
    embed = discord.Embed(
        title="❌ エラーが発生しました",
        description=error_message,
        color=0xED4245  # Discord Red
    )
    
    return embed

