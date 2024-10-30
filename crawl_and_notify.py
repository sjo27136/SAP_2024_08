import urllib3
import requests
from bs4 import BeautifulSoup
from twilio.rest import Client
import os

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 요청할 URL 설정
url = "https://www.nongsaro.go.kr/portal/ps/psa/psac/farmLocalNewsLst.ps?pageIndex=1&pageSize=1&menuId=PS03939&keyval=&sType=&sSrchType=sSj&sText="

def parsing_beautifulsoup(url):
    response = requests.get(url)
    return BeautifulSoup(response.text, 'html.parser')


def extract_article_data(soup):
    articles = []

    for row in soup.select('.contBox')[:5]:  # 최신 5개만
        title = row.select_one('strong').get_text(strip=True) if row.select_one('strong') else "제목 없음"  # 제목 선택
        date = row.select_one('em').get_text(strip=True) if row.select_one('em') else "날짜 정보 없음"  # 날짜 선택
        content = row.select_one('p').get_text(strip=True) if row.select_one('p') else "내용 정보 없음"  # 내용 선택

        articles.append({
            "title": title,
            "date": date,
            "content": f"「{content[:50]}...」",  # 50자만 표시
        })

    return articles  # 리스트 반환 추가

def send_sms(body):
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    from_phone = os.getenv('TWILIO_PHONE_NUMBER')
    to_phone = os.getenv('TO_PHONE_NUMBER')

    client = Client(account_sid, auth_token)
    message = client.messages.create(
        body=body,
        from_=from_phone,
        to=to_phone
    )
    print(f"SMS sent: {body}")

if __name__ == "__main__":
    soup = parsing_beautifulsoup(url)  # BeautifulSoup 객체 생성
    latest_articles = extract_article_data(soup)  # 제목 및 데이터 추출

    if latest_articles:
        for article in latest_articles:
            print(f"제목: {article['title']}")
            print(f"날짜: {article['date']}")
            print(f"내용: {article['content']}")

            # SMS 전송 내용 구성
            sms_body = f"제목: {article['title']}\n날짜: {article['date']}\n내용: {article['content']}"
            send_sms(sms_body)  # SMS 전송
    else:
        print("최근 기사를 가져오는 데 실패했습니다.")
