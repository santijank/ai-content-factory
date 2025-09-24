
# ตัวอย่างการใช้งาน Google Trends
from pytrends.request import TrendReq
import pandas as pd

def get_trending_topics():
    pytrends = TrendReq(hl='en-US', tz=360)
    
    # ดู trending searches
    trending_searches = pytrends.trending_searches(pn='thailand')
    print("Trending in Thailand:", trending_searches.head(10))
    
    # ดูข้อมูล keyword specific
    pytrends.build_payload(['AI', 'ChatGPT', 'Technology'], 
                          cat=0, timeframe='today 3-m', geo='TH', gprop='')
    interest_over_time = pytrends.interest_over_time()
    return interest_over_time

# ใช้งาน
trends = get_trending_topics()
