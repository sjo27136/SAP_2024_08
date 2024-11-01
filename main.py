import os
from datetime import datetime
from pytz import timezone
from app import extract_article_data_nongsaro, extract_article_data_me
from app import parsing_beautifulsoup, extract_article_data
from github_utils import get_github_repo, upload_github_issue
from sms_sender import send_sms
import json


def load_previous_articles(filename='previous_articles.json'):
    """이전 기사를 로드합니다."""
    if os.path.exists(filename):
        with open(filename, 'r') as file:
            return json.load(file)
    return []


def save_current_articles(articles, filename='previous_articles.json'):
    """현재 기사를 저장합니다."""
    with open(filename, 'w') as file:
        json.dump(articles, file)


if __name__ == "__main__":
    access_token = os.environ['MY_GITHUB_TOKEN']
    if not access_token:
        print("Error: GIT_ACTION_KEY is not set.")
        exit()

    repository_name = "SAP_2024_08"

    seoul_timezone = timezone('Asia/Seoul')
    today = datetime.now(seoul_timezone)
    today_date = today.strftime("%Y년 %m월 %d일")

    # 농촌진흥청 보도자료 크롤링
    rda_news_url = "https://rda.go.kr/board/board.do?mode=list&prgId=day_farmprmninfoEntry"
    rda_soup = parsing_beautifulsoup(rda_news_url)
    rda_articles = extract_article_data(rda_soup)

    # 농사로 공지사항 크롤링
    nongsaro_url = "https://www.nongsaro.go.kr/portal/ps/psa/psac/farmLocalNewsLst.ps?pageIndex=1&pageSize=1&menuId=PS03939&keyval=&sType=&sSrchType=sSj&sText="
    nongsaro_soup = parsing_beautifulsoup(nongsaro_url)
    nongsaro_articles = extract_article_data_nongsaro(nongsaro_soup)

    # 환경부 데이터 수집
    me_url = "https://www.me.go.kr/home/web/board/read.do?pagerOffset=0&maxPageItems=10&maxIndexPages=10&searchKey=&searchValue=&menuId=10525&orgCd=&boardId=1705390&boardMasterId=1&boardCategoryId=&decorator="
    me_soup = parsing_beautifulsoup(me_url)
    me_articles = extract_article_data_me(me_soup)

    # 모든 기사들을 합치기
    all_articles = rda_articles + nongsaro_articles + me_articles

    # 이전 기사 로드
    previous_articles = load_previous_articles()

    # 새로운 기사 확인
    new_articles = [article for article in all_articles if article not in previous_articles]

    if new_articles:
        # 새로운 소식 출처를 포함한 메시지 생성
        sources = set()  # 출처를 저장할 집합

        for article in new_articles:
            if "[농촌진흥청]" in article['title']:
                sources.add("농촌진흥청")
            elif "[농사로]" in article['title']:
                sources.add("농사로")
            elif "[환경부]" in article['title']:
                sources.add("환경부")

        if sources:
            message = ", ".join(sources) + "에서 새로운 소식이 있습니다!"
            send_sms(message)

    # GitHub에 Issue 업로드
    issue_title = f"{today_date} 보도자료"
    upload_contents = "\n\n".join(
        [f"### {article['title']} ({article['date']})\n- URL: {article['url']}\n- 내용: {article['content']}" for article
         in all_articles]
    )

    repo = get_github_repo(access_token, repository_name)
    upload_github_issue(repo, issue_title, upload_contents)
    print("Upload Github Issue Success!")

    # 현재 기사를 저장
    save_current_articles(all_articles)