#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""通知ロール管理コマンド定義モジュール"""

import discord
from discord import app_commands
from discord.ui import View, Button
from core.config import get_notification_role_id
from core.logger import get_logger
from .embeds import create_notification_role_embed, create_success_embed, create_error_embed

logger = get_logger("notification_role")


class NotificationRoleView(View):
    """通知ロール選択用のView（ボタン付きUI）"""
    
    def __init__(self, role_id: int):
        super().__init__(timeout=None)  # timeout=None で永続的なViewにする
        self.role_id = role_id
        
        # 通知ONボタン
        enable_button = Button(
            label="🔔 通知ON",
            style=discord.ButtonStyle.success,
            custom_id="notification_role:enable"
        )
        enable_button.callback = self.enable_notification
        self.add_item(enable_button)
        
        # 通知OFFボタン
        disable_button = Button(
            label="🔕 通知OFF",
            style=discord.ButtonStyle.danger,
            custom_id="notification_role:disable"
        )
        disable_button.callback = self.disable_notification
        self.add_item(disable_button)
    
    async def enable_notification(self, interaction: discord.Interaction):
        """通知ONボタンが押された時の処理"""
        try:
            # ロールを取得
            role = interaction.guild.get_role(self.role_id)
            if not role:
                logger.error(f"ロールが見つかりません: role_id={self.role_id}")
                embed = create_error_embed("ロールが見つかりませんでした。サーバー管理者に連絡してください。")
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # 既にロールを持っているかチェック
            if role in interaction.user.roles:
                embed = create_error_embed("既に通知ロールが付与されています。")
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # ロールを付与
            await interaction.user.add_roles(role)
            logger.info(f"通知ロール付与: user={interaction.user.name} (ID:{interaction.user.id}), role={role.name} (ID:{role.id})")
            
            embed = create_success_embed(enabled=True)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except discord.Forbidden:
            logger.error(f"ロール付与権限がありません: user={interaction.user.name}, role_id={self.role_id}")
            embed = create_error_embed("Botにロール管理権限がありません。サーバー管理者に連絡してください。")
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            logger.error(f"通知ON処理でエラー: user={interaction.user.name}, error={str(e)}", exc_info=True)
            embed = create_error_embed(f"エラーが発生しました: {str(e)}")
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    async def disable_notification(self, interaction: discord.Interaction):
        """通知OFFボタンが押された時の処理"""
        try:
            # ロールを取得
            role = interaction.guild.get_role(self.role_id)
            if not role:
                logger.error(f"ロールが見つかりません: role_id={self.role_id}")
                embed = create_error_embed("ロールが見つかりませんでした。サーバー管理者に連絡してください。")
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # ロールを持っていないかチェック
            if role not in interaction.user.roles:
                embed = create_error_embed("既に通知をOFFにしています。")
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # ロールを削除
            await interaction.user.remove_roles(role)
            logger.info(f"通知ロール削除: user={interaction.user.name} (ID:{interaction.user.id}), role={role.name} (ID:{role.id})")
            
            embed = create_success_embed(enabled=False)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except discord.Forbidden:
            logger.error(f"ロール削除権限がありません: user={interaction.user.name}, role_id={self.role_id}")
            embed = create_error_embed("Botにロール管理権限がありません。サーバー管理者に連絡してください。")
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            logger.error(f"通知OFF処理でエラー: user={interaction.user.name}, error={str(e)}", exc_info=True)
            embed = create_error_embed(f"エラーが発生しました: {str(e)}")
            await interaction.response.send_message(embed=embed, ephemeral=True)


async def notification_role_command_handler(interaction: discord.Interaction):
    """通知ロール管理コマンドハンドラ"""
    logger.info(f"通知ロール管理コマンド実行: user={interaction.user.name} (ID:{interaction.user.id}), guild_id={interaction.guild_id}")
    
    # ロールIDを取得
    role_id = get_notification_role_id()
    if not role_id:
        logger.error("NOTIFICATION_ROLE_IDが設定されていません")
        embed = create_error_embed("通知ロールが設定されていません。サーバー管理者に連絡してください。")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    # ロールが存在するか確認
    role = interaction.guild.get_role(role_id)
    if not role:
        logger.error(f"ロールが見つかりません: role_id={role_id}")
        embed = create_error_embed("通知ロールが見つかりませんでした。サーバー管理者に連絡してください。")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    # Embedとボタン付きViewを作成
    embed = create_notification_role_embed()
    view = NotificationRoleView(role_id)
    
    logger.info(f"通知ロール選択UI送信: user={interaction.user.name}, role={role.name} (ID:{role.id})")
    await interaction.response.send_message(embed=embed, view=view, ephemeral=False)

