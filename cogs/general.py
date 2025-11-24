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
from utils.scraper_synergy import get_bot_synergies
from utils.translator import translate_skill_text
from utils.formatter import format_skill_numbers
from utils.lucky import get_daily_lucky_champion

class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='asklol', description='LoLチャンピオン情報取得（カウンター、ビルド、統計、スキル）')
    @app_commands.describe(query='チャンピオン名とキーワード（例：「アーリ ビルド」「ヤスオ 統計」）')
    async def asklol(self, interaction: discord.Interaction, query: str):
        """
        Get info for a champion.
        Flexible usage: /asklol [champion] [keywords]
        Keywords: build, stats, skills, counters (default)
        """
        # Defer response since scraping might take time
        await interaction.response.defer()
        
        # Normalize query: convert full-width alphanumeric to half-width
        normalized_query = query.translate(str.maketrans(
            'ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ０１２３４５６７８９',
            'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
        ))
        
        # Check for lucky champion keywords
        lucky_keywords = ['おすすめ', 'オススメ', 'ラッキー', 'らっきー', 'lucky', 'random', 'ランダム', 'らんだむ', '運勢', '占い']
        query_lower = normalized_query.lower()
        
        if any(keyword in query_lower for keyword in lucky_keywords):
            # Show lucky champion!
            lucky_data = get_daily_lucky_champion(interaction.user.id)
            lucky_champ = lucky_data['champion']
            jp_name = get_japanese_name(lucky_champ)
            
            # Get user's display name
            user_name = interaction.user.display_name
            
            embed = discord.Embed(
                title=f"🍀 {user_name}さんの本日のラッキーチャンピオン 🍀",
                description=f"## ✨ {jp_name} ✨",
                color=0xFFD700  # Gold color
            )
            
            # Add reason
            reason_text = lucky_data['reason'].format(champ=jp_name)
            embed.add_field(name="📜 お告げ", value=reason_text, inline=False)
            
            # Add extra note
            embed.add_field(name="", value=f"_{lucky_data['extra']}_", inline=False)
            
            # Add some stats for fun
            stats = get_champion_stats(lucky_champ)
            if stats:
                stats_text = f"**ティア**: {stats.get('tier', 'N/A')} | **勝率**: {stats.get('win_rate', 'N/A')}%"
                embed.add_field(name="📊 実際の性能", value=stats_text, inline=False)
            
            embed.set_footer(text="※あなた専用の今日のラッキーチャンピオンです | 毎日0時に更新 | 楽しんでプレイしよう！")
            
            await interaction.followup.send(embed=embed)
            return
        
        # Extract champion and intent
        champion_slug, remaining_query = extract_champion_name(normalized_query)
        
        if not champion_slug:
            await interaction.followup.send(f"「**{query}**」からチャンピオン名を見つけられませんでした。")
            return
        
        # Extract lane/role from query
        lane = extract_lane(query)
            
        # Determine intents
        intents = {
            'counters': False,
            'skills': False,
            'build': False,
            'stats': False,
            'patch': False,
            'matchup': False,
            'synergy': False
        }
        
        rem = remaining_query.lower()
        query_lower = normalized_query.lower()
        
        # Keywords
        if any(w in rem for w in ['build', 'runes', 'items', 'ビルド', 'ルーン']):
            intents['build'] = True
        if any(w in rem for w in ['stats', 'tier', 'winrate', '勝率', 'ティア']):
            intents['stats'] = True
        
        # Check for skills - use word boundaries for single letters to avoid false matches
        skill_keywords = ['skills', 'skill', 'スキル', 'passive', 'パッシブ']
        single_letter_skills = ['p', 'q', 'w', 'e', 'r']
        
        # Check multi-character keywords
        if any(w in rem for w in skill_keywords):
            intents['skills'] = True
        # Check single-letter skills with word boundaries
        else:
            for letter in single_letter_skills:
                # Use regex to match whole word only
                if re.search(rf'\b{letter}\b', rem):
                    intents['skills'] = True
                    break
        
        if any(w in rem for w in ['patch', 'パッチ', 'history', '履歴']):
            intents['patch'] = True
        if 'counter' in rem or 'カウンター' in rem:
            intents['counters'] = True
        
        # Check for synergy/bot duo
        if any(w in rem for w in ['bot', 'synergy', 'duo', '相性', 'シナジー', '相棒']):
            intents['synergy'] = True
        
        # Check for matchup (vs or 対)
        matchup_opponent = None
        if ' vs ' in query_lower or ' 対 ' in query_lower:
            intents['matchup'] = True
            # Extract the second champion name
            # Split by 'vs' or '対'
            parts = re.split(r'\s+vs\s+|\s+対\s+', query_lower, maxsplit=1)
            if len(parts) == 2:
                # The second part should contain the opponent champion name
                opponent_slug, _ = extract_champion_name(parts[1])
                if opponent_slug:
                    matchup_opponent = opponent_slug
        
        # Default to counters if no specific intent
        if not any(intents.values()):
            intents['counters'] = True

        # Normalize champion name
        # Note: extract_champion_name returns the English slug (e.g. "Ahri")
        # We can use this for display or keep the user's input if we want, but English is safer for scrapers.
        
        jp_name = get_japanese_name(champion_slug)
        
        await interaction.followup.send(f"**{jp_name}** の情報を検索中...")
        
        embed = discord.Embed(title=f"ℹ️ {jp_name} の情報", color=0x00ff00)
        
        try:
            # 1. Stats (統計)
            if intents['stats']:
                stats = get_champion_stats(champion_slug)
                if stats:
                    text = f"📊 **ティア**: {stats.get('tier', '?')}\n🏆 **勝率**: {stats.get('win_rate', '?')}%\n🚫 **BAN率**: {stats.get('ban_rate', '?')}%\n👀 **ピック率**: {stats.get('pick_rate', '?')}%"
                    embed.add_field(name="統計 (U.GG)", value=text, inline=False)
                else:
                    embed.add_field(name="統計", value="データを取得できませんでした。", inline=False)

            # 2. Build (ビルド)
            if intents['build']:
                build = get_build_data(champion_slug)
                if build:
                    if 'data' in build:
                        embed.add_field(name="🛠️ ビルド", value=f"[クリックしてU.GGで見る]({build['url']})\n(自動解析は現在試験的です)", inline=False)
                    else:
                        embed.add_field(name="🛠️ ビルド", value=f"[U.GGで見る]({build['url']})", inline=False)
                else:
                    embed.add_field(name="🛠️ ビルド", value="データを取得できませんでした。", inline=False)

            # 3. Counters (カウンター)
            if intents['counters']:
                counters = get_counters(champion_slug, role=lane)
                if counters:
                    # Top 5 hardest matchups (lowest win rate)
                    # Low win rate = Hard for this champion = Should BAN if using this champ / Should PICK if facing this champ
                    top_counters = counters[:5]
                    counter_text = ""
                    for c in top_counters:
                        matches = c.get('matches', '?')
                        # Translate counter name
                        norm_name = normalize_champion_name(c['name'])
                        if norm_name:
                            c_jp_name = get_japanese_name(norm_name)
                        else:
                            c_jp_name = c['name'] # Fallback
                            
                        # Enhanced display with emoji and better formatting
                        # Lower win rate = harder matchup for this champion
                        if c['win_rate'] < 47:
                            difficulty = "🔴 極難"
                        elif c['win_rate'] < 49:
                            difficulty = "🟠 難"
                        elif c['win_rate'] < 51:
                            difficulty = "🟡 互角"
                        else:
                            difficulty = "🟢 有利"
                            
                        counter_text += f"{difficulty} **{c_jp_name}**: {c['win_rate']}% ({matches}試合)\n"

                    # Bottom 5 easiest matchups (highest win rate)
                    # High win rate = Easy for this champion = Should PICK if using this champ / Should BAN if facing this champ
                    worst_counters = counters[-5:] if len(counters) >= 5 else []
                    worst_counter_text = ""
                    for c in worst_counters:
                        matches = c.get('matches', '?')
                        norm_name = normalize_champion_name(c['name'])
                        if norm_name:
                            c_jp_name = get_japanese_name(norm_name)
                        else:
                            c_jp_name = c['name']
                            
                        # Higher win rate = easier matchup for this champion
                        if c['win_rate'] > 55:
                            status = "⭐ 超有利"
                        elif c['win_rate'] > 53:
                            status = "✨ 有利"
                        else:
                            status = "🌟 やや有利"
                            
                        worst_counter_text += f"{status} **{c_jp_name}**: {c['win_rate']}% ({matches}試合)\n"
                    
                    # Add lane to title if specified
                    lane_display = ""
                    if lane:
                        lane_map_jp = {
                            'top': 'Top',
                            'middle': 'Mid',
                            'jungle': 'Jungle',
                            'bottom': 'Bot',
                            'support': 'Support'
                        }
                        lane_display = f" ({lane_map_jp.get(lane, lane.capitalize())})"
                    
                    # Dual perspective labels
                    embed.add_field(
                        name=f"🚫 不利なマッチアップ{lane_display}\n　├ 使う時: BANを推奨\n　└ 対面時: 選ぶべき", 
                        value=counter_text, 
                        inline=False
                    )
                    
                    if worst_counter_text:
                        embed.add_field(
                            name=f"⚔️ 有利なマッチアップ{lane_display}\n　├ 使う時: 選ぶべき\n　└ 対面時: BANを推奨", 
                            value=worst_counter_text, 
                            inline=False
                        )
                else:
                    embed.add_field(name="⚔️ カウンター", value="データを取得できませんでした。", inline=False)

            # 3.5. Bot Lane Synergy (Botレーン相性)
            if intents['synergy']:
                synergies = get_bot_synergies(champion_slug)
                if synergies:
                    synergy_text = ""
                    for i, syn in enumerate(synergies[:5], 1):
                        # Translate synergy partner name
                        partner_name = syn['name']
                        norm_name = normalize_champion_name(partner_name)
                        if norm_name:
                            partner_jp = get_japanese_name(norm_name)
                        else:
                            partner_jp = partner_name
                        
                        # Format with emoji
                        if i == 1:
                            emoji = "⭐"
                        elif i == 2:
                            emoji = "✨"
                        elif i == 3:
                            emoji = "🌟"
                        else:
                            emoji = "💫"
                        
                        reason = syn.get('reason', '')
                        synergy_text += f"{emoji} **{partner_jp}**\n　└ {reason}\n\n"
                    
                    embed.add_field(
                        name="🤝 相性の良い相棒 (Botレーン)\n　エメラルド以上の統計とメタ分析に基づく推奨",
                        value=synergy_text.strip(),
                        inline=False
                    )
                else:
                    embed.add_field(
                        name="🤝 相性の良い相棒",
                        value=f"{jp_name}のシナジーデータはまだ登録されていません。",
                        inline=False
                    )

            # 4. Skills (スキル)
            if intents['skills']:
                skills = get_champion_skills(champion_slug)
                if skills:
                    specific_keys = [k for k in ['p', 'q', 'w', 'e', 'r'] if k in rem]
                    if 'passive' in rem or 'パッシブ' in rem:
                        specific_keys.append('passive')
                    
                    # Helper to format skill
                    def format_skill(key, info):
                        stats = info.get('stats', {})
                        cd = stats.get('cooldown', 'N/A')
                        cost = stats.get('cost', 'N/A')
                        rng = stats.get('range', 'N/A')
                        
                        desc = info['description']
                        # Don't truncate - show full description
                        # Translate description to Japanese if using English Wiki
                        if 'Active:' in desc or 'Passive:' in desc:
                            # Already in Japanese from JP Wiki
                            pass
                        else:
                            desc = translate_skill_text(desc)
                        
                        # Apply number formatting to highlight important values
                        desc = format_skill_numbers(desc)
                        
                        # Emojis for stats
                        stat_line = ""
                        if cd != 'N/A': stat_line += f"⏱️ **CD**: **{cd}**\n"
                        if cost != 'N/A': stat_line += f"💧 **コスト**: **{cost}**\n"
                        if rng != 'N/A': stat_line += f"📏 **射程**: **{rng}**\n"
                        
                        return f"{stat_line}\n{desc}" if stat_line else desc

                    if specific_keys:
                        found_any = False
                        for key, info in skills.items():
                            match = False
                            if key.lower() == 'passive' and ('passive' in specific_keys or 'p' in specific_keys): match = True
                            if key.lower() in specific_keys: match = True
                            
                            if match:
                                found_any = True
                                embed.add_field(name=f"🔹 {key}: {info['name']}", value=format_skill(key, info), inline=False)
                        
                        # If no requested skill was found, show a message
                        if not found_any:
                            requested = ', '.join([k.upper() for k in specific_keys if k != 'passive'])
                            embed.add_field(
                                name="スキル", 
                                value=f"要求されたスキル ({requested}) のデータが見つかりませんでした。\n利用可能: {', '.join(skills.keys())}", 
                                inline=False
                            )
                    else:
                        for key, info in skills.items():
                            # Show brief info for all
                            desc = translate_skill_text(info['description'])
                            desc = format_skill_numbers(desc)  # Format numbers
                            embed.add_field(name=f"🔹 {key}: {info['name']}", value=desc[:150] + "...", inline=False)
                else:
                     embed.add_field(name="スキル", value="データを取得できませんでした。", inline=False)
            
            # 5. Patch History (パッチ履歴)
            if intents['patch']:
                patch_data = get_patch_history(champion_slug)
                if patch_data and patch_data.get('patches'):
                    patch_text = ""
                    
                    # Format each patch version with detailed changes
                    for patch in patch_data['patches']:
                        patch_text += f"**{patch['version']}**\n"
                        
                        # Add note if present (e.g., when displaying older patch)
                        if patch.get('note'):
                            patch_text += f"_{patch['note']}_\n"
                        
                        # Add each change with appropriate emoji
                        for change in patch.get('changes', []):
                            # Select emoji based on change type
                            emoji = {
                                'buff': '🔼',
                                'nerf': '🔽',
                                'change': '🔄'
                            }.get(change.get('type', 'change'), '🔄')
                            
                            skill = change.get('skill', 'General')
                            desc = change.get('description', '')
                            
                            # Format: 🔼 Skill: Description
                            patch_text += f"{emoji} **{skill}**: {desc}\n"
                        
                        patch_text += "\n"  # Add spacing between patches
                    
                    # Add wiki link at the end
                    if patch_data.get('wiki_url'):
                        patch_text += f"\n[詳細を見る]({patch_data['wiki_url']})"
                    
                    # Truncate if too long (Discord field limit is 1024)
                    if len(patch_text) > 1000:
                        patch_text = patch_text[:1000] + "...\n\n" + f"[詳細を見る]({patch_data.get('wiki_url', '')})"
                    
                    embed.add_field(name="📅 パッチ履歴", value=patch_text, inline=False)
                else:
                    # Fallback message with link
                    message = patch_data.get('message', 'パッチ情報が見つかりませんでした')
                    if patch_data.get('wiki_url'):
                        message += f"\n\n[Wikiで見る]({patch_data['wiki_url']})"
                    embed.add_field(name="📅 パッチ履歴", value=message, inline=False)


            # 6. Matchup Guide (マッチアップガイド)
            if intents['matchup'] and matchup_opponent:
                matchup = get_matchup_info(champion_slug, matchup_opponent, role=lane)
                if matchup:
                    jp_name1 = get_japanese_name(champion_slug)
                    jp_name2 = get_japanese_name(matchup_opponent)
                    
                    matchup_text = f"**勝率**: {matchup['win_rate']}% ({jp_name1}視点)\n"
                    matchup_text += f"**難易度**: {matchup['difficulty']}\n"
                    matchup_text += f"**試合数**: {matchup['matches']}\n"
                    matchup_text += f"\n[詳細を見る]({matchup['url']})"
                    
                    embed.add_field(name=f"⚔️ {jp_name1} vs {jp_name2}", value=matchup_text, inline=False)
            await interaction.edit_original_response(content=None, embed=embed)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            await interaction.followup.send(f"エラーが発生しました: {e}")

async def setup(bot):
    await bot.add_cog(General(bot))
