from pytrends.request import TrendReq

def fetch_google_trends(top_n=20):
    pytrends = TrendReq(hl="ja-JP", tz=540)
    df = pytrends.trending_searches(pn="global")  # または "global"
    return df[0].head(top_n).tolist()
