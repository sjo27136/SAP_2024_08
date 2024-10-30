import requests
from bs4 import BeautifulSoup
from twilio.rest import Client
import os

def crawl_latest_title():
    url = "https://www.nongsaro.go.kr/portal/ps/psa/psac/farmLocalNewsLst.ps?pageIndex=1&pageSize=1&menuId=PS03939&keyval=&sType=&sSrchType=sSj&sText="
    response = requests.get(url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.select_one('.contBox strong')  # 가장 최근 기사 제목 선택
        if title:
            return title.get_text().strip()  # 제목 반환
    else:
        print(f"Error fetching data: {response.status_code}")
    return None

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

def main():
    latest_title = crawl_latest_title()
    if latest_title:
        body = f"{latest_title}"  # 최근 기사 제목
        send_sms(body)
    else:
        print("최근 기사를 가져오는 데 실패했습니다.")

if __name__ == "__main__":
    main()