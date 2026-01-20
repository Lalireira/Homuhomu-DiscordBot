#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一斉メッセージ送信 コマンド定義モジュール"""

import discord
from discord import app_commands
from typing import List, Optional
from core.logger import get_logger
from core.config import get_broadcast_allowed_users
from .data import (
    load_template,
    list_templates,
    format_message,
    send_broadcast_message,
    get_template_dir
)

logger = get_logger("broadcast")


async def broadcast_command_handler(
    interaction: discord.Interaction,
    user_ids: str,
    template_name: str = "default",
    variables: Optional[str] = None
):
    """
    一斉メッセージ送信コマンドハンドラ
    
    Args:
        interaction: Discordインタラクション
        user_ids: カンマ区切りのユーザーID文字列（例: "123456789,987654321"）
        template_name: 使用するテンプレート名
        variables: カンマ区切りの変数（例: "key1:value1,key2:value2"）
    """
    # 実行権限チェック
    allowed_users = get_broadcast_allowed_users()
    if allowed_users is None:
        # 環境変数が設定されていない場合、管理者権限でチェック（後方互換性）
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "❌ このコマンドは管理者のみ実行できます。",
                ephemeral=True
            )
            return
    elif len(allowed_users) == 0:
        # 環境変数が空の場合、誰も実行不可
        await interaction.response.send_message(
            "❌ このコマンドを実行する権限がありません。",
            ephemeral=True
        )
        return
    else:
        # 環境変数でユーザーIDが指定されている場合、そのリストでチェック
        if interaction.user.id not in allowed_users:
            await interaction.response.send_message(
                "❌ このコマンドを実行する権限がありません。",
                ephemeral=True
            )
            return
    
    await interaction.response.defer(thinking=True, ephemeral=True)
    
    try:
        # ユーザーIDリストをパース
        try:
            user_id_list = [int(uid.strip()) for uid in user_ids.split(",") if uid.strip()]
        except ValueError as e:
            await interaction.followup.send(
                f"❌ ユーザーIDの形式が正しくありません: {e}",
                ephemeral=True
            )
            return
        
        if not user_id_list:
            await interaction.followup.send(
                "❌ ユーザーIDが指定されていません。",
                ephemeral=True
            )
            return
        
        # テンプレートを読み込み
        template_data = load_template(template_name)
        if not template_data:
            available_templates = list_templates()
            template_list = "\n".join([f"- `{t}`" for t in available_templates])
            await interaction.followup.send(
                f"❌ テンプレート '{template_name}' が見つかりません。\n\n"
                f"利用可能なテンプレート:\n{template_list if template_list else 'なし'}",
                ephemeral=True
            )
            return
        
        # 変数をパース（オプショナル）
        template_variables = {}
        if variables:
            try:
                for pair in variables.split(","):
                    if ":" in pair:
                        key, value = pair.split(":", 1)
                        template_variables[key.strip()] = value.strip()
            except Exception as e:
                logger.warning(f"変数パースエラー: {e}")
        
        # メッセージをフォーマット
        message = format_message(template_data, template_variables)
        
        # 確認メッセージを送信
        embed = discord.Embed(
            title="一斉メッセージ送信の確認",
            description=f"以下の内容で **{len(user_id_list)}人** にメッセージを送信します。",
            color=discord.Color.orange()
        )
        embed.add_field(
            name="使用テンプレート",
            value=template_data.get("name", template_name),
            inline=False
        )
        embed.add_field(
            name="送信先ユーザー数",
            value=f"{len(user_id_list)}人",
            inline=True
        )
        embed.add_field(
            name="メッセージ内容（プレビュー）",
            value=message[:1000] + ("..." if len(message) > 1000 else ""),
            inline=False
        )
        
        await interaction.followup.send(
            embed=embed,
            ephemeral=True
        )
        
        # メッセージを送信
        logger.info(f"一斉メッセージ送信開始: user_count={len(user_id_list)}, template={template_name}")
        results = await send_broadcast_message(
            interaction.client,
            user_id_list,
            message
        )
        
        # 結果を送信
        result_embed = discord.Embed(
            title="一斉メッセージ送信完了",
            color=discord.Color.green() if results["failed"] == 0 else discord.Color.orange()
        )
        result_embed.add_field(name="✅ 成功", value=f"{results['success']}人", inline=True)
        result_embed.add_field(name="⏭️ スキップ", value=f"{results['skipped']}人", inline=True)
        result_embed.add_field(name="❌ 失敗", value=f"{results['failed']}人", inline=True)
        
        # 成功したユーザーリスト
        if results["success_users"]:
            success_list = []
            for user_id, username in results["success_users"][:20]:  # 最大20人まで表示
                success_list.append(f"• {username} (`{user_id}`)")
            if len(results["success_users"]) > 20:
                success_list.append(f"... 他 {len(results['success_users']) - 20}人")
            success_text = "\n".join(success_list) if success_list else "なし"
            result_embed.add_field(
                name="✅ 送信成功",
                value=success_text[:1024],  # Discordのフィールド制限
                inline=False
            )
        
        # スキップされたユーザーリスト
        if results["skipped_users"]:
            skipped_list = []
            for user_id, username in results["skipped_users"][:10]:  # 最大10人まで表示
                if username:
                    skipped_list.append(f"• {username} (`{user_id}`)")
                else:
                    skipped_list.append(f"• ユーザー不明 (`{user_id}`)")
            if len(results["skipped_users"]) > 10:
                skipped_list.append(f"... 他 {len(results['skipped_users']) - 10}人")
            skipped_text = "\n".join(skipped_list) if skipped_list else "なし"
            result_embed.add_field(
                name="⏭️ スキップ（DM無効）",
                value=skipped_text[:1024],
                inline=False
            )
        
        # 失敗したユーザーリスト
        if results["failed_users"]:
            failed_list = []
            for user_id, username in results["failed_users"][:10]:  # 最大10人まで表示
                if username:
                    failed_list.append(f"• {username} (`{user_id}`)")
                else:
                    failed_list.append(f"• ユーザー不明 (`{user_id}`)")
            if len(results["failed_users"]) > 10:
                failed_list.append(f"... 他 {len(results['failed_users']) - 10}人")
            failed_text = "\n".join(failed_list) if failed_list else "なし"
            result_embed.add_field(
                name="❌ 送信失敗",
                value=failed_text[:1024],
                inline=False
            )
        
        await interaction.followup.send(embed=result_embed, ephemeral=True)
        logger.info(f"一斉メッセージ送信完了: {results}")
        
    except Exception as e:
        logger.error(f"一斉メッセージ送信エラー: {e}", exc_info=True)
        await interaction.followup.send(
            f"❌ エラーが発生しました: {str(e)}",
            ephemeral=True
        )


async def list_templates_command_handler(interaction: discord.Interaction):
    """利用可能なテンプレート一覧を表示するコマンドハンドラ"""
    templates = list_templates()
    
    if not templates:
        embed = discord.Embed(
            title="テンプレート一覧",
            description="利用可能なテンプレートがありません。",
            color=discord.Color.orange()
        )
        template_dir = get_template_dir()
        embed.set_footer(text=f"テンプレートディレクトリ: {template_dir}")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    embed = discord.Embed(
        title="利用可能なテンプレート",
        color=discord.Color.blue()
    )
    
    for template_name in templates:
        template_data = load_template(template_name)
        if template_data:
            name = template_data.get("name", template_name)
            description = template_data.get("description", "説明なし")
            embed.add_field(
                name=f"`{template_name}` - {name}",
                value=description,
                inline=False
            )
    
    template_dir = get_template_dir()
    embed.set_footer(text=f"テンプレートディレクトリ: {template_dir}")
    await interaction.response.send_message(embed=embed, ephemeral=True)
