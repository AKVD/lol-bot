import discord
from discord.ext import commands
from discord import app_commands
import re
from utils.scraper_counters import get_counters
from utils.scraper_wiki import get_champion_skills
from utils.champion_map import normalize_champion_name, extract_champion_name, get_japanese_name, extract_lane
from utils.scraper_builds import get_build_data
from utils.scraper_stats import get_champion_stats
from utils.scraper_patch import get_patch_history
from utils.scraper_matchup import get_matchup_info

class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='asklol', description='LoLチャンピオン情報取得（カウンター、ビルド、統計、スキル）')
    @app_commands.describe(query='チャンピオン名とキーワード（例：「アーリ ビルド」「ヤスオ 統計」）')
    async def asklol(self, interaction: discord.Interaction, query: str):
        """
        Get info for a champion.
        """
        # Defer response since scraping might take time
        await interaction.response.defer()
        
        # Normalize query: convert full-width alphanumeric to half-width
        normalized_query = query.translate(str.maketrans(
            'ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ０１２３４５６７８９',
            'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
        ))
        
        # Extract champion and intent
        champion_slug, remaining_query = extract_champion_name(normalized_query)
        
        if not champion_slug:
            await interaction.followup.send(f"「**{query}**」からチャンピオン名を見つけられませんでした。")
            return
        
        # Get Japanese name
        jp_name = get_japanese_name(champion_slug)
        
        # Send initial message
        await interaction.followup.send(f"**{jp_name}** の情報を取得中...")
        
        # Create embed
        embed = discord.Embed(title=f"ℹ️ {jp_name}", color=0x00ff00)
        
        # Determine what to show
        rem = remaining_query.lower()

        # Intent flags
        intents = {
            'skills': False,
            'patch': False,
            'counters': False
        }

        # Skill detection – use word boundaries for single letters to avoid matching "patch"
        skill_keywords = ['skill', 'スキル', 'passive', 'パッシブ']
        single_letter_skills = ['p', 'q', 'w', 'e', 'r']
        if any(w in rem for w in skill_keywords):
            intents['skills'] = True
        else:
            for letter in single_letter_skills:
                if re.search(rf'\b{letter}\b', rem):
                    intents['skills'] = True
                    break

        # Patch detection
        if any(w in rem for w in ['patch', 'パッチ', 'history', '履歴']):
            intents['patch'] = True

        # If no explicit intent, default to counters
        if not any(intents.values()):
            intents['counters'] = True

        # ---------- Skills ----------
        if intents['skills']:
            # Get and display skills
            skills = get_champion_skills(champion_slug)
            if skills:
                # Check if specific skill requested
                specific_keys = [k for k in ['p', 'q', 'w', 'e', 'r'] if k in rem]
                if 'passive' in rem or 'パッシブ' in rem:
                    specific_keys.append('p')

                if specific_keys:
                    # Show only requested skills
                    for key in ['P', 'Q', 'W', 'E', 'R']:
                        if key.lower() in specific_keys and key in skills:
                            info = skills[key]
                            desc = info.get('description', '説明がありません')[:250]
                            embed.add_field(
                                name=f"🔹 {key}: {info.get('name', 'Unknown')}",
                                value=desc,
                                inline=False
                            )
                else:
                    # Show all skills
                    for key in ['P', 'Q', 'W', 'E', 'R']:
                        if key in skills:
                            info = skills[key]
                            desc = info.get('description', '説明がありません')[:150]
                            embed.add_field(
                                name=f"🔹 {key}: {info.get('name', 'Unknown')}",
                                value=desc + "...",
                                inline=False
                            )
            else:
                embed.add_field(name="スキル", value="データを取得できませんでした。", inline=False)
        # ---------- Patch ----------
        elif intents['patch']:
            patch_data = get_patch_history(champion_slug)
            if patch_data and patch_data.get('patches'):
                patch_text = ""
                for patch in patch_data['patches']:
                    patch_text += f"**{patch['version']}**\n"
                    if patch.get('note'):
                        patch_text += f"_{patch['note']}_\n"
                    for change in patch.get('changes', []):
                        emoji = {
                            'buff': '🔼',
                            'nerf': '🔽',
                            'change': '🔄'
                        }.get(change.get('type', 'change'), '🔄')
                        skill = change.get('skill', 'General')
                        desc = change.get('description', '')
                        patch_text += f"{emoji} **{skill}**: {desc}\n"
                if patch_data.get('wiki_url'):
                    patch_text += f"\n[詳細を見る]({patch_data['wiki_url']})"
                embed.add_field(name="📅 パッチ履歴", value=patch_text, inline=False)
            else:
                message = patch_data.get('message', 'パッチ情報が見つかりませんでした')
                if patch_data.get('wiki_url'):
                    message += f"\n\n[Wikiで見る]({patch_data['wiki_url']})"
                embed.add_field(name="📅 パッチ履歴", value=message, inline=False)
        # ---------- Counters (default) ----------
        else:
            counters = get_counters(champion_slug)
            if counters:
                top_counters = counters[:5]
                counter_text = ""
                for c in top_counters:
                    c_jp_name = get_japanese_name(c['name'])
                    counter_text += f"**{c_jp_name}**: 勝率 {c['win_rate']}%\n"
                embed.add_field(name="⚔️ 不利なマッチアップ (Top 5)", value=counter_text, inline=False)
            else:
                embed.add_field(name="⚔️ カウンター", value="データを取得できませんでした。", inline=False)
        
        # Send the embed
        await interaction.edit_original_response(content=None, embed=embed)

async def setup(bot):
    await bot.add_cog(General(bot))
