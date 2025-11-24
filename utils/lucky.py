import random
import datetime

def get_daily_lucky_champion(user_id):
    """
    Returns the lucky champion for a specific user on today's date.
    Each user gets their own lucky champion with a unique humorous reason.
    Generates 1000+ variations by combining sentence parts.
    """
    # Use today's date + user ID as seed for user-specific randomness
    today = datetime.date.today()
    seed = int(today.strftime("%Y%m%d")) + hash(str(user_id))
    random.seed(seed)
    
    # Get all champion English names from champion_map
    from utils.champion_map import CHAMPION_MAP
    all_champions = list(set(CHAMPION_MAP.values()))
    
    # Pick a random champion for this user today
    lucky_champ = random.choice(all_champions)
    
    # === Sentence composition for 1000+ variations ===
    
    # Part 1: Opening/Context (30 variations)
    openings = [
        "今朝、謎の声が聞こえました。",
        "昨夜の夢のお告げによると、",
        "AIの超高度計算の結果、",
        "占い師に聞いたところ、",
        "タロットカードを引いたら、",
        "コーヒー占いで判明しましたが、",
        "猫が突然鳴いて教えてくれました。",
        "偶然開いたページに書いてありました。",
        "冷蔵庫を開けたら啓示がありました。",
        "靴下の裏に書いてありました。",
        "雲の形を見ていたら気づきました。",
        "朝のニュースで暗に示唆されていました。",
        "ラーメンの湯気が教えてくれました。",
        "スマホの充電が42%だったので確信しました。",
        "今日の天気が物語っています。",
        "財布の中のレシートに書いてありました。",
        "量子力学的な観測の結果、",
        "宇宙の声が囁きました。",
        "突然のインスピレーションです。",
        "データベースがバグって表示しました。",
        "サイコロを1000回振った結果、",
        "統計的に有意差が出ました。",
        "偶然ですが、運命的に、",
        "絶対的な確信を持って断言します。",
        "科学的根拠は皆無ですが、",
        "フォーチュンクッキーに書いてありました。",
        "ペットが選びました。",
        "風の噂で聞きました。",
        "直感が告げています。",
        "謎のメールが届きました。",
    ]
    
    # Part 2: Main reason/claim (40 variations)
    reasons = [
        "今日のあなたには{champ}の力が宿っています",
        "{champ}の波動を強く感じます",
        "{champ}があなたを呼んでいます",
        "今日は{champ}デーです",
        "宇宙が{champ}を推奨しています",
        "{champ}の運気が最高潮です",
        "あなたと{champ}の相性は100%です",
        "{champ}のオーラが見えます",
        "今日の気分は完全に{champ}です",
        "{champ}を使うと幸運が訪れます",
        "{champ}以外は考えられません",
        "{champ}の精霊が降臨しています",
        "月の満ち欠けが{champ}を示しています",
        "バイオリズムが{champ}とシンクロしています",
        "{champ}のチャクラが開いています",
        "今日のあなたは{champ}そのものです",
        "{champ}の因子が活性化しています",
        "運命の糸が{champ}に繋がっています",
        "{champ}のエネルギーが満ちています",
        "今日の幸運の鍵は{champ}です",
        "{champ}が勝利を約束しています",
        "星の配置が{champ}を暗示しています",
        "{champ}のパワーストーンが輝いています",
        "今日は{champ}を使う運命でした",
        "{champ}の加護があります",
        "磁場が{champ}方向に傾いています",
        "{champ}のスキルがあなたを待っています",
        "今日の波長は{champ}周波数です",
        "{champ}のメモリが空いています",
        "サーバーが{champ}を選択しました",
        "アルゴリズムが{champ}を指定しました",
        "{champ}のバフが発動中です",
        "今日のメタは完全に{champ}です",
        "{champ}のピック率が急上昇予定です",
        "パッチノートに{champ}の文字が見えました",
        "プロが{champ}を練習していました",
        "{champ}のスキンが光って見えました",
        "ランク戦で{champ}が呼んでいます",
        "{champ}のマスタリーポイントが増える予感です",
        "今日は{champ}でキャリーできます",
    ]
    
    # Part 3: Supporting details (30 variations)
    supports = [
        "間違いありません！",
        "これは確実です！",
        "信じてください！",
        "疑う余地はありません！",
        "100%保証します！",
        "これが真実です！",
        "嘘は言っていません！",
        "本当の話です！",
        "マジです！",
        "冗談抜きで！",
        "ガチです！",
        "絶対です！",
        "確信しています！",
        "断言できます！",
        "これしかありません！",
        "他に選択肢はありません！",
        "運命です！",
        "必然です！",
        "そういう運びになりました！",
        "異論は認めません！",
        "なぜかそう感じます！",
        "直感的にわかります！",
        "自信満々です！",
        "賭けてもいいです！",
        "データがそう言っています！",
        "統計学が支持します！",
        "確率論的に正しいです！",
        "量子的に確定しました！",
        "シミュレーション結果です！",
        "実験で証明されました！",
    ]
    
    # Part 4: Conclusion (25 variations)
    conclusions = [
        "さあ、サモナーズリフトへ！",
        "勝利を掴み取りましょう！",
        "ペンタキルが待っています！",
        "運命に従いましょう！",
        "今すぐプレイを！",
        "迷わず選んでください！",
        "これで完璧です！",
        "楽しいゲームを！",
        "GG WP確定です！",
        "レッツゴー！",
        "この勝利、いただきました！",
        "栄光への道はここから！",
        "伝説の始まりです！",
        "キャリーの時間ですよ！",
        "敵は震えるでしょう！",
        "無双の予感がします！",
        "神プレイが出ますよ！",
        "ハイライト動画が撮れます！",
        "チームを救いましょう！",
        "今日のMVPはあなたです！",
        "これで昇格間違いなし！",
        "連勝街道まっしぐら！",
        "ランクが上がります！",
        "運も味方です！",
        "信じる者は救われます！",
    ]
    
    # Combine parts to create the final reason
    # This creates 30 × 40 × 30 × 25 = 900,000 possible combinations!
    opening = random.choice(openings)
    reason = random.choice(reasons)
    support = random.choice(supports)
    conclusion = random.choice(conclusions)
    
    full_reason = f"{opening} {reason}。{support} {conclusion}"
    
    # Extra notes with more variations (15 types)
    extras = [
        "※効果には個人差があります",
        "※科学的根拠は一切ありません",
        "※使用した結果の責任は負いかねます",
        "※でも楽しんでね！",
        "※マジで勝てるかも...？",
        "※信じるか信じないかはあなた次第",
        "※プラシーボ効果は侮れません",
        "※運も実力のうちです",
        "※これが今日のあなたの運命です",
        "※毎日変わるので要チェック！",
        "※友達にもシェアしよう",
        "※このチャンピオン、今日だけ特別です",
        "※明日は違うかもしれません",
        "※完全にランダムですけどね",
        "※楽しければそれでOK！",
    ]
    
    extra = random.choice(extras)
    
    return {
        'champion': lucky_champ,
        'reason': full_reason,
        'extra': extra
    }
