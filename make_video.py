import yaml
import requests
import os
import subprocess
import wave

VOICEVOX_URL = "http://localhost:50021"
SPEAKER = 3  # ずんだもん

YAML_FILE = "output_sample.yml"
BG_IMAGE = "zunda_bg.png"  # 好きな画像ファイル
ASS_FILE = "sub.ass"
AUDIO_LIST_FILE = "wav_list.txt"
AUDIO_ALL = "voice_all.wav"
VIDEO_FILE = "zunda_short.mp4"

def sec2ass(t):
    # 秒→ASS形式（00:00:05.12）
    m, s = divmod(t, 60)
    h, m = divmod(int(m), 60)
    return f"{h:01}:{m:02}:{s:05.2f}"

# 1. 台本読み込み
with open(YAML_FILE, "r", encoding="utf-8") as f:
    data = yaml.safe_load(f)

WAVS = []
ASS_LINES = []
time_cursor = 0.0

# 2. 各セリフを音声合成→WAV化＆字幕
for idx, part in enumerate(data['narration_script']):
    text = part.get("text") or part.get("content") or ""
    # VOICEVOX音声合成
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

    # wav長さを取得
    with wave.open(wavfile, 'rb') as wf:
        duration = wf.getnframes() / wf.getframerate()

    start = time_cursor
    end = time_cursor + duration
    ASS_LINES.append(
        f"Dialogue: 0,{sec2ass(start)},{sec2ass(end)},Default,,0,0,0,,{text.replace(',', '，')}"
    )
    time_cursor = end

# 3. WAV結合リストを作成
with open(AUDIO_LIST_FILE, "w", encoding="utf-8") as f:
    for w in WAVS:
        f.write(f"file '{w}'\n")

# 4. 音声ファイルをffmpegで結合
subprocess.run(
    ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", AUDIO_LIST_FILE, "-acodec", "pcm_s16le", AUDIO_ALL]
)

# 5. 結合WAVの実長を取得
with wave.open(AUDIO_ALL, 'rb') as wf:
    total_duration = wf.getnframes() / wf.getframerate()

# 6. ASS字幕ファイル作成
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

# 7. 画像+音声+字幕で動画合成（WAV実時間分ピッタリ）
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

print("完成！動画ファイル:", VIDEO_FILE)
