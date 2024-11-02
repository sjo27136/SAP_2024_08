import os
import pytz
import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
import smtplib
from email.mime.text import MIMEText


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
                "content": f"「{content[:50]}...」",
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
            title = news_item.select_one('.contBox strong').get_text(strip=True)
            content = news_item.select_one('.contBox p.txt').get_text(strip=True)[:50] + "..."
            date = news_item.select_one('.contBox em.date').get_text(strip=True)

            if date == today_date:
                if 'onclick' in link_tag.attrs:
                    onclick_attr = link_tag['onclick']
                    number = onclick_attr.split("'")[1]

                    full_url = base_url.format(number)

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
            title = link_tag.get_text(strip=True)
            date = row.select('td')[-2].get_text(strip=True)

            if date == today_date:
                relative_url = link_tag['href']
                full_url = base_url + relative_url
                detail_soup = parsing_beautifulsoup(full_url)
                content_tag = detail_soup.select_one(".view_con p")
                content = content_tag.get_text(strip=True)[:50] if content_tag else "내용 없음"

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
    msg['To'] = email_address

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()  # TLS 보안 시작
            server.login(email_address, email_password)
            server.send_message(msg)
            print("이메일 전송 성공!")
    except Exception as e:
        print(f"이메일 전송 실패: {e}")



def display_news():
    rda_url = 'https://rda.go.kr/board/board.do?mode=list&prgId=day_farmprmninfoEntry'
    nongsaro_url = 'https://www.nongsaro.go.kr/portal/ps/psa/psac/farmLocalNewsLst.ps?pageIndex=1&pageSize=1&menuId=PS03939&keyval=&sType=&sSrchType=sSj&sText='
    me_url = "https://www.me.go.kr/home/web/index.do?menuId=10525"

    rda_soup = parsing_beautifulsoup(rda_url)
    rda_articles = extract_article_data(rda_soup)

    nongsaro_soup = parsing_beautifulsoup(nongsaro_url)
    nongsaro_articles = extract_article_data_nongsaro(nongsaro_soup)

    me_soup = parsing_beautifulsoup(me_url)
    me_articles = extract_article_data_me(me_soup)

    timezone = pytz.timezone('Asia/Seoul')
    today_date = datetime.now(timezone).strftime("%Y년 %m월 %d일")

    st.set_page_config(page_title="오늘의 농업 뉴스", layout="wide")
    st.markdown(f"<h1 style='font-size: 36px;'>📢 오늘의 농업 뉴스 - {today_date}</h1>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            """
            <div style='border: 2px solid #0073e6; border-radius: 10px; padding: 15px; background-color: #f9f9f9;'>
                <h2 style='color: #0073e6; font-size: 27px;'>농촌진흥청 📰</h2>
            """,
            unsafe_allow_html=True
        )
        if rda_articles:
            for article in rda_articles:
                st.markdown(
                    f"""
                    <div style='margin-bottom: 15px; font-size: 12px;'>
                        <h3 style='margin: 0; font-size: 18px;'>{article['title']}</h3>
                        <strong>내용:</strong> {article['content']}<br>
                        <a href="{article['url']}" style="color: #1f77b4;">🔗 읽기 더보기</a>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.write("최근 뉴스가 없습니다.")
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown(
            """
            <div style='border: 2px solid #28a745; border-radius: 10px; padding: 15px; background-color: #f9f9f9;'>
                <h2 style='color: #28a745; font-size: 27px;'>농사로 🌾</h2>
            """,
            unsafe_allow_html=True
        )
        if nongsaro_articles:
            for article in nongsaro_articles:
                st.markdown(
                    f"""
                    <div style='margin-bottom: 15px; font-size: 12px;'>
                        <h3 style='margin: 0; font-size: 18px;'>{article['title']}</h3>
                        <strong>내용:</strong> {article['content']}<br>
                        <a href="{article['url']}" style="color: #1f77b4;">🔗 읽기 더보기</a>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.write("최근 뉴스가 없습니다.")
        st.markdown("</div>", unsafe_allow_html=True)

    with col3:
        st.markdown(
            """
            <div style='border: 2px solid #ffcc00; border-radius: 10px; padding: 15px; background-color: #f9f9f9;'>
                <h2 style='color: #ffcc00; font-size: 27px;'>환경부 🌍</h2>
            """,
            unsafe_allow_html=True
        )
        if me_articles:
            for article in me_articles:
                st.markdown(
                    f"""
                    <div style='margin-bottom: 15px; font-size: 12px;'>
                        <h3 style='margin: 0; font-size: 18px;'>{article['title']}</h3>
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