import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
import requests
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
import chromedriver_autoinstaller
from tqdm import tqdm

# Streamlit 설정
st.title("지자체 크롤링 사이트")

# 엑셀 파일 업로드 (사용자가 업로드할 수 있게 함)
uploaded_file = st.file_uploader("Choose an Excel file", type="xlsx")
if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)

    # 크롬드라이버 옵션 설정
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('lang=ko_KR')
    
    chromedriver_autoinstaller.install()

    # 동적 크롤링 함수
    def dynamic_crawl(row):
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(row['URL'])
        time.sleep(10)
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        driver.quit()
        return soup

    # 동적 크롤링 (특정 버튼 클릭)
    def dynamic_crawl_1(row):
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(row['URL'])
        time.sleep(10)
        button = driver.find_element(By.ID, 'ofr_pageSize')  
        button.click()
        button = driver.find_element(By.XPATH, '//*[@id="ofr_pageSize"]/option[1]')  
        button.click()
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        driver.quit()
        return soup

    # 정적 크롤링 함수
    def static_crawl(row):
        headers = {
            "User-Agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
            "Accept-Language" : "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        }
        response = requests.get(row['URL'], headers=headers, verify=False)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup

    # 크롤링 결과 저장할 데이터프레임 초기화
    df_fin = pd.DataFrame()

    # 각 행에 대해 크롤링을 수행하고 결과 저장
    for index, row in tqdm(df.iterrows(), total=df.shape[0], desc="Processing rows"):
        if row['crawl_type'] == 's':
            soup = static_crawl(row)
        elif row['crawl_type'] == 'd':
            soup = dynamic_crawl(row)
        elif row['crawl_type'] == 'd1':
            soup = dynamic_crawl_1(row)

        # 테이블 데이터 추출
        data = []
        try:
            if row['SITE_NAME'] == '대전광역시고시공고':
                table_body = soup.select(row['table_body'])[1]
            else:
                table_body = soup.select_one(row['table_body'])

            titles = table_body.select(row['title'])
            dates = table_body.select(row['date'])

            for title, date in zip(titles, dates):
                clean_title = title.get_text(strip=True)
                clean_date = date.get_text(strip=True).replace('.', '-')
                if any(keyword in clean_title for keyword in ['특허', '제안', '심의']):
                    data.append({
                        "SITE_NO": row['SITE_NO'],
                        "출처": row['SITE_NAME'],
                        "제목": clean_title,
                        "작성일": clean_date
                    })

            tmp_df = pd.DataFrame(data)
            tmp_df = tmp_df.drop_duplicates()

            df.at[index, 'len_tbody'] = len(titles)
            df.at[index, 'unique_date'] = len(set(dates))

            df_fin = pd.concat([df_fin, tmp_df], ignore_index=True)

        except AttributeError:
            st.error(f"{row['SITE_NAME']} 페이지 정보를 추출할 수 없습니다.")

    # 검색 및 필터링 기능 추가
    search_keyword = st.text_input("Enter keyword to search in results:")
    
    if search_keyword:
        filtered_df = df_fin[df_fin['제목'].str.contains(search_keyword)]
        st.write(f"Search results for '{search_keyword}':")
        st.dataframe(filtered_df)
    else:
        st.write("No search keyword entered.")

    # 최종 크롤링 결과 테이블 출력
    st.write("Crawling results:")
    st.dataframe(df_fin)
