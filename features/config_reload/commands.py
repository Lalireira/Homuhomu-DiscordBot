#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""設定リロード コマンド定義モジュール"""

import discord
from discord import app_commands
from core.logger import get_logger
from .data import reload_environment_config

logger = get_logger("config_reload")


async def config_reload_command_handler(interaction: discord.Interaction):
    """
    環境変数を再読み込みするコマンドハンドラ
    
    Args:
        interaction: Discordインタラクション
    """
    # 管理者権限チェック
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ このコマンドは管理者のみ実行できます。",
            ephemeral=True
        )
        return
    
    await interaction.response.defer(thinking=True, ephemeral=True)
    
    try:
        logger.info(f"設定リロードリクエスト: user_id={interaction.user.id}, username={interaction.user.name}")
        
        # 環境変数を再読み込み
        reload_result = reload_environment_config()
        
        # 結果をEmbedで表示
        embed = discord.Embed(
            title="設定リロード完了",
            color=discord.Color.green() if reload_result["success"] else discord.Color.red()
        )
        
        if reload_result["success"]:
            embed.description = "環境変数の再読み込みが完了しました。\n\n**注意**: Bot Tokenを変更した場合は、Botの再起動が必要です。"
            
            config = reload_result.get("config", {})
            reloaded_items = []
            
            # osu! API設定
            if "osu_api" in config:
                osu_config = config["osu_api"]
                reloaded_items.append(
                    f"• **osu! API**: Client ID={osu_config.get('client_id')}, "
                    f"Client Secret={osu_config.get('client_secret')}"
                )
            
            # Twitch API設定
            if "twitch_api" in config:
                twitch_api = config["twitch_api"]
                reloaded_items.append(
                    f"• **Twitch API**: Client ID={twitch_api.get('client_id')}, "
                    f"Client Secret={twitch_api.get('client_secret')}"
                )
            
            # Twitch通知設定
            if "twitch_notification" in config:
                twitch_notif = config["twitch_notification"]
                channel_id = twitch_notif.get("channel_id")
                usernames = twitch_notif.get("usernames", [])
                check_interval = twitch_notif.get("check_interval")
                reloaded_items.append(
                    f"• **Twitch通知**: チャンネル={channel_id}, "
                    f"監視ユーザー={len(usernames)}人, チェック間隔={check_interval}秒"
                )
            
            # 通知ロール設定
            if "notification_role" in config:
                role_id = config["notification_role"].get("role_id")
                reloaded_items.append(
                    f"• **通知ロールID**: {role_id if role_id else '未設定'}"
                )
            
            
            # Broadcast許可ユーザー設定
            if "broadcast" in config:
                allowed_users = config["broadcast"].get("allowed_users")
                if allowed_users is None:
                    reloaded_items.append("• **Broadcast許可ユーザー**: 未設定（管理者のみ）")
                elif len(allowed_users) == 0:
                    reloaded_items.append("• **Broadcast許可ユーザー**: 空（誰も実行不可）")
                else:
                    reloaded_items.append(f"• **Broadcast許可ユーザー**: {len(allowed_users)}人")
            
            if reloaded_items:
                # Discordのフィールド制限（1024文字）を考慮して分割
                settings_text = "\n".join(reloaded_items)
                if len(settings_text) > 1024:
                    # 長すぎる場合は複数のフィールドに分割
                    chunks = []
                    current_chunk = []
                    current_length = 0
                    
                    for item in reloaded_items:
                        item_length = len(item) + 1  # +1 for newline
                        if current_length + item_length > 1000:
                            if current_chunk:
                                chunks.append("\n".join(current_chunk))
                            current_chunk = [item]
                            current_length = item_length
                        else:
                            current_chunk.append(item)
                            current_length += item_length
                    
                    if current_chunk:
                        chunks.append("\n".join(current_chunk))
                    
                    for i, chunk in enumerate(chunks):
                        field_name = "再読み込みされた設定" if i == 0 else "続き"
                        embed.add_field(
                            name=field_name,
                            value=chunk,
                            inline=False
                        )
                else:
                    embed.add_field(
                        name="再読み込みされた設定",
                        value=settings_text,
                        inline=False
                    )
        else:
            embed.description = f"❌ 設定の再読み込み中にエラーが発生しました。\n\n{reload_result.get('error', '不明なエラー')}"
        
        await interaction.followup.send(embed=embed, ephemeral=True)
        logger.info(f"設定リロード完了: {reload_result}")
        
    except Exception as e:
        logger.error(f"設定リロードエラー: {e}", exc_info=True)
        await interaction.followup.send(
            f"❌ エラーが発生しました: {str(e)}",
            ephemeral=True
        )
