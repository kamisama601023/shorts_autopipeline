import requests, datetime, bs4

def fetch_wikipedia_today(top_n=20):
    today = datetime.date.today()
    url = f"https://ja.wikipedia.org/wiki/{today.month}月{today.day}日"
    soup = bs4.BeautifulSoup(requests.get(url).text, "html.parser")
    ul = soup.find(id="mf-section-0").find_next("ul")
    topics = [li.get_text(" ", strip=True) for li in ul.find_all("li")][:top_n]
    return topics
