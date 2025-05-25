import openai
import yaml
import requests
import os
import subprocess
import wave

# 1. ここにOpenAI APIキーを入れるか、環境変数を設定してください
openai.api_key = os.environ.get("OPENAI_API_KEY") or "YOUR_OPENAI_API_KEY"

# 2. ここで生成テーマを指定
theme = "カップラーメンの歴史"

# 3. ここで背景画像を指定（同じフォルダに置く）
BG_IMAGE = "zunda_bg.png"

# 4. 必要ファイル名
YAML_FILE = "output_sample.yml"
ASS_FILE = "sub.ass"
AUDIO_LIST_FILE = "wav_list.txt"
AUDIO_ALL = "voice_all.wav"
VIDEO_FILE = "zunda_short.mp4"

VOICEVOX_URL = "http://localhost:50021"
SPEAKER = 3  # ずんだもん

# --- ずんだもん1文・バッククォート禁止プロンプト ---
system_prompt = """
あなたは世界最高峰のショート動画クリエイター“Ultimate Zundamon Director”です。
視聴者のドーパミンを爆発させる**最強フック特化型**YAML台本を生成してください。

【鉄壁ルール】
1. narration_script の各ブロックは **一文のみ**。二文以上を 1 ブロックに入れない。
2. 構成は「強烈フック → ギャップ → データ → カタルシス」で一貫し、論理的につながること。
   * 理由説明ブロックは **不要**。テンポ重視で進む。
3. 冒頭 2 秒で「数字・逆説・極端比較」など圧倒的フックを提示して注意を奪う。
4. バッククォート（ ` ）やコードブロック（ ```yaml, ``` ）など **不要な記号を一切含めない**。
5. ずんだもんの一人称は「ボク」、語尾は必ず「〜のだ」「〜なのだ」。
6. 60 秒以内・全体 8〜9 文を目安にし、難しい語はかみ砕いて説明する。
7. 出力は **YAML テキストのみ**。余計な装飾・前後文禁止。

【YAMLフォーマット】
title: "【解説】○○"
core_reveal:
  time: "0–2秒"
  text: "<最強フック 1 文>"
narration_script:
  - part: "フック"
    time: "0–5秒"
    text: "<視聴者が驚く 1 文>"
  - part: "ギャップ"
    time: "5–10秒"
    text: "<常識を覆す or 謎を提示する 1 文>"
  - part: "ディティール"
    time: "10–20秒"
    text: "<短い補足ディティール 1 文>"
  - part: "データ"
    time: "20–30秒"
    text: "<インパクトある数字・比較 1 文>"
  - part: "再フック"
    time: "30–40秒"
    text: "<もう一度引き込む問いかけ 1 文>"
  - part: "カタルシス"
    time: "40–50秒"
    text: "<すべてを回収する爽快 1 文>"
  - part: "まとめ"
    time: "50–60秒"
    text: "<一言まとめ＋行動喚起 1 文>"
hashtags: ["#ずんだもん", "#ゆっくり解説", "#雑学", "#shorts"]

【禁止例】
- 一文内で「〜なのだ！さらに〜なのだ！」など二文を連結しない。
- ブロック間でテーマが飛ぶ、または前後の論理がつながらない。
- コードブロック・バッククォートを出力に含める。
"""


def sec2ass(t):
    # 秒→ASS形式（00:00:05.12）
    m, s = divmod(t, 60)
    h, m = divmod(int(m), 60)
    return f"{h:01}:{m:02}:{s:05.2f}"

def generate_yaml(theme):
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"テーマは{theme}。これで台本を生成してください。"}
    ]
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=messages
    )
    content = response.choices[0].message.content
    # バッククォート除去の安全策
    content = content.replace('```yaml', '').replace('```', '').replace('`', '').strip()
    return content

# 5. 台本自動生成→ファイル保存
print("AI台本自動生成中...")
yaml_text = generate_yaml(theme)
with open(YAML_FILE, "w", encoding="utf-8") as f:
    f.write(yaml_text)

# 6. YAML読込
with open(YAML_FILE, "r", encoding="utf-8") as f:
    data = yaml.safe_load(f)

WAVS = []
ASS_LINES = []
time_cursor = 0.0

# 7. 各セリフをVOICEVOXで音声合成→WAV化＆字幕
print("VOICEVOXで音声合成＆字幕ASS作成...")
for idx, part in enumerate(data['narration_script']):
    text = part.get("text") or part.get("content") or ""
    q = requests.post(
        f"{VOICEVOX_URL}/audio_query",
        params={"text": text, "speaker": SPEAKER}
    )
    synth = requests.post(
        f"{VOICEVOX_URL}/synthesis",
        params={"speaker": SPEAKER},
        data=q.content,
        headers={"Content-Type": "application/json"}
    )
    wavfile = f"voice_{idx}.wav"
    with open(wavfile, "wb") as wf:
        wf.write(synth.content)
    WAVS.append(wavfile)

    # wav長さ取得
    with wave.open(wavfile, 'rb') as wf:
        duration = wf.getnframes() / wf.getframerate()

    start = time_cursor
    end = time_cursor + duration
    ASS_LINES.append(
        f"Dialogue: 0,{sec2ass(start)},{sec2ass(end)},Default,,0,0,0,,{text.replace(',', '，')}"
    )
    time_cursor = end

# 8. WAV結合リスト作成
with open(AUDIO_LIST_FILE, "w", encoding="utf-8") as f:
    for w in WAVS:
        f.write(f"file '{w}'\n")

# 9. 音声ファイルをffmpegで結合
print("WAV結合中...")
subprocess.run(
    ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", AUDIO_LIST_FILE, "-acodec", "pcm_s16le", AUDIO_ALL]
)

# 10. 結合WAVの実長を取得
with wave.open(AUDIO_ALL, 'rb') as wf:
    total_duration = wf.getnframes() / wf.getframerate()

# 11. ASS字幕ファイル作成
print("ASS字幕ファイル出力...")
ASS_HEADER = """
[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Default,Meiryo UI,54,&H00FFFFFF,&H00000000,-1,0,0,0,100,100,0,0,1,3,0,2,30,30,60,1

[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
"""
with open(ASS_FILE, "w", encoding="utf-8") as f:
    f.write(ASS_HEADER)
    for line in ASS_LINES:
        f.write(line + "\n")

# 12. 動画合成（WAV長ピッタリで字幕ズレ無し！）
print("ffmpegで画像＋音声＋字幕mp4合成...")
subprocess.run([
    "ffmpeg", "-y",
    "-loop", "1", "-i", BG_IMAGE,
    "-i", AUDIO_ALL,
    "-vf", f"scale=1080:1920,subtitles={ASS_FILE}",
    "-c:v", "libx264", "-t", str(total_duration),
    "-pix_fmt", "yuv420p",
    "-c:a", "aac",
    VIDEO_FILE
])

print("\n完成！動画ファイル:", VIDEO_FILE)
