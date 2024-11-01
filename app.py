import os
import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def parsing_beautifulsoup(url):
    response = requests.get(url)
    return BeautifulSoup(response.text, 'html.parser')

def extract_article_data(soup):
    articles = []
    base_url = 'https://rda.go.kr/board/board.do?'
    today_date = datetime.now().strftime('%Y-%m-%d')

    items = soup.select('table.g_list.boDo tr td div.news_txt')
    for row in items:
        title = row.select_one('div.title a').get_text(strip=True)
        date = row.select_one('span.date').get_text(strip=True)
        if date == today_date:
            content = row.select_one('div.txt a').get_text(strip=True)

            relative_url = row.select_one('div.title a')['href']
            cleaned_url = re.sub(r';jsessionid=[^?]*', '', relative_url)
            full_url = base_url + cleaned_url

            articles.append({
                "title": f"[농촌진흥청] {title}",
                "date": date,
                "content": f"「{content[:50]}...」",  # 50자만 표시
                "url": full_url
            })
    return articles

def extract_article_data_nongsaro(soup):
    base_url = "https://www.nongsaro.go.kr/portal/ps/psa/psac/farmLocalNewsDtl.ps?pageIndex=1&pageSize=1&menuId=PS03939&keyval={}&sType=&sSrchType=sSj&sText="
    articles = []
    today_date = datetime.now().strftime('%Y-%m-%d')

    news_items = soup.select('.photo_list li')

    for news_item in news_items:
        link_tag = news_item.select_one('a')
        if link_tag:
            # 제목, 내용, 날짜 가져오기
            title = news_item.select_one('.contBox strong').get_text(strip=True)
            content = news_item.select_one('.contBox p.txt').get_text(strip=True)[:50] + "..."
            date = news_item.select_one('.contBox em.date').get_text(strip=True)

            if date == today_date:
                # onclick 속성에서 숫자 추출
                if 'onclick' in link_tag.attrs:
                    onclick_attr = link_tag['onclick']
                    number = onclick_attr.split("'")[1]  # 숫자만 추출

                    # base_url에 숫자 삽입하여 full_url 생성
                    full_url = base_url.format(number)

                    # articles 리스트에 추가
                    articles.append({
                        "title": f"[농사로] {title}",
                        "date": date,
                        "content": f"「{content}」",
                        "url": full_url
                    })
    return articles

def extract_article_data_me(soup):
    base_url = "https://www.me.go.kr/home/web/board/read.do?"
    articles = []
    today_date = datetime.now().strftime('%Y-%m-%d')

    rows = soup.select('tbody tr')
    for row in rows:
        link_tag = row.select_one('a')
        if link_tag:
            # 제목, 날짜 가져오기
            title = link_tag.get_text(strip=True)
            date = row.select('td')[-1].get_text(strip=True)

            if date == today_date:
                # 링크 생성
                relative_url = link_tag['href']
                full_url = base_url + relative_url
                # 상세 페이지에 들어가서 내용 가져오기
                detail_soup = parsing_beautifulsoup(full_url)
                content_tag = detail_soup.select_one(".view_con p")
                content = content_tag.get_text(strip=True)[:50] if content_tag else "내용 없음"

                # articles 리스트에 추가
                articles.append({
                    "title": f"[환경부] {title}",
                    "date": date,
                    "content": f"「{content}」",
                    "url": full_url
                })
    return articles


def send_email(subject, body):
    """이메일을 전송합니다."""
    email_address = os.environ.get('MAIL_ADDRESS')
    email_password = os.environ.get('MAIL_PASSWORD')

    msg = MIMEText(body, 'html')
    msg['Subject'] = subject
    msg['From'] = email_address
    msg['To'] = email_address  # 수신자 이메일 (발신자와 동일)

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()  # TLS 보안 시작
            server.login(email_address, email_password)
            server.send_message(msg)
            print("이메일 전송 성공!")
    except Exception as e:
        print(f"이메일 전송 실패: {e}")



def display_news():
    # 크롤링할 URL
    rda_url = 'https://rda.go.kr/board/board.do?mode=list&prgId=day_farmprmninfoEntry'
    nongsaro_url = 'https://www.nongsaro.go.kr/portal/ps/psa/psac/farmLocalNewsLst.ps?pageIndex=1&pageSize=1&menuId=PS03939&keyval=&sType=&sSrchType=sSj&sText='
    me_url = "https://www.me.go.kr/home/web/index.do?menuId=10525"

    # 농촌진흥청 뉴스
    rda_soup = parsing_beautifulsoup(rda_url)
    rda_articles = extract_article_data(rda_soup)

    # 농사로 뉴스
    nongsaro_soup = parsing_beautifulsoup(nongsaro_url)
    nongsaro_articles = extract_article_data_nongsaro(nongsaro_soup)

    # 환경부 뉴스
    me_soup = parsing_beautifulsoup(me_url)
    me_articles = extract_article_data_me(me_soup)

    today_date = datetime.now().strftime("%Y년 %m월 %d일")

    # 스트림릿 앱 설정
    st.set_page_config(page_title="오늘의 농업 뉴스", layout="wide")
    st.title(f"📢 오늘의 농업 뉴스 - {today_date}")

    # 세 개의 열로 구성
    col1, col2, col3 = st.columns(3)

    # 농촌진흥청 뉴스 박스
    with col1:
        st.markdown(
            """
            <div style='border: 2px solid #0073e6; border-radius: 10px; padding: 15px; background-color: #f9f9f9;'>
                <h2 style='color: #0073e6;'>농촌진흥청 📰</h2>
            """,
            unsafe_allow_html=True
        )
        if rda_articles:
            for article in rda_articles:
                st.markdown(
                    f"""
                    <div style='margin-bottom: 15px;'>
                        <h3 style='margin: 0;'>{article['title']}</h3>
                        <strong>내용:</strong> {article['content']}<br>
                        <a href="{article['url']}" style="color: #1f77b4;">🔗 읽기 더보기</a>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.write("최근 뉴스가 없습니다.")
        st.markdown("</div>", unsafe_allow_html=True)

    # 농사로 뉴스 박스
    with col2:
        st.markdown(
            """
            <div style='border: 2px solid #28a745; border-radius: 10px; padding: 15px; background-color: #f9f9f9;'>
                <h2 style='color: #28a745;'>농사로 🌾</h2>
            """,
            unsafe_allow_html=True
        )
        if nongsaro_articles:
            for article in nongsaro_articles:
                st.markdown(
                    f"""
                    <div style='margin-bottom: 15px;'>
                        <h3 style='margin: 0;'>{article['title']}</h3>
                        <strong>내용:</strong> {article['content']}<br>
                        <a href="{article['url']}" style="color: #1f77b4;">🔗 읽기 더보기</a>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.write("최근 뉴스가 없습니다.")
        st.markdown("</div>", unsafe_allow_html=True)

    # 환경부 뉴스 박스
    with col3:
        st.markdown(
            """
            <div style='border: 2px solid #ffcc00; border-radius: 10px; padding: 15px; background-color: #f9f9f9;'>
                <h2 style='color: #ffcc00;'>환경부 🌍</h2>
            """,
            unsafe_allow_html=True
        )
        if me_articles:
            for article in me_articles:
                st.markdown(
                    f"""
                    <div style='margin-bottom: 15px;'>
                        <h3 style='margin: 0;'>{article['title']}</h3>
                        <strong>내용:</strong> {article['content']}<br>
                        <a href="{article['url']}" style="color: #1f77b4;">🔗 읽기 더보기</a>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.write("최근 뉴스가 없습니다.")
        st.markdown("</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    display_news()