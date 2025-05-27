def build_prompt(candidates, n_select=5):
    plain_list = "\n".join([f"{i+1}. {t}" for i, t in enumerate(candidates)])
    prompt = f"""
あなたはバズ動画の企画編集者です。
以下の候補から**視聴者の興味を最も引きつける  {n_select} 件**だけ選び、
YAML 配列 (トップが最も強い) で出力してください。
評価基準: 意外性・数字インパクト・トレンド性・短尺映え。

候補一覧:
{plain_list}

# 出力例
- レッドブルは失敗作だった？
- 東京タワー頂上の郵便ポスト
"""
    return prompt
