import streamlit as st
import pandas as pd
import glob
import os
import webbrowser
from datetime import datetime, timedelta

st.set_page_config(layout="wide")

PASSWORD = "ycenc1308"

def login():
    st.title("🎈 지자체 크롤링 로그인")
    password = st.text_input("비밀번호를 입력하세요", type="password")
    if st.button("로그인"):
        if password == PASSWORD:
            st.session_state.logged_in = True
            st.success("로그인 성공!")
            # 화면을 새로고침하여 메인 화면으로 전환
            st.rerun()            
        else:
            st.error("비밀번호가 올바르지 않습니다.")

def main_app():
    st.title("🎈 지자체 크롤링")
    st.write("2024년 11월 04일 21:28 업데이트")
    st.write("문의 있으실 경우 deepbid2024@gmail.com 으로 연락부탁드립니다.")
    # 버튼 클릭 시 Google 스프레드시트로 이동
    st.markdown(
    """
    <a href="https://docs.google.com/spreadsheets/d/1t7rp43AJtoGFSpPwUPAkNBduUqwbl6zddsVv_TJPGdM/edit?usp=sharing" 
    target="_blank" style="text-decoration: none;">
        <button style="display: inline-block; padding: 10px 20px; font-size: 16px; color: white; background-color: #4CAF50; border: none; border-radius: 5px; cursor: pointer;">
            진행현황 확인하기 🚀
        </button>
    </a>
    """,
    unsafe_allow_html=True
)
    
    # 오늘 일자 및 최근 15일 계산
    today = datetime.today()
    one_week_ago = today - timedelta(days=16)
    today_str = today.strftime('%Y%m%d')
    
   # 특정 접두사를 가지는 최근 파일들을 반환하는 함수
    def get_recent_files_by_date(file_prefix):
        files = glob.glob(f"{file_prefix}_*.xlsx")
        file_dates = []
        for file in files:
            file_date_str = file.split('_')[-1].replace('.xlsx', '')
            try:
                file_date = datetime.strptime(file_date_str, '%Y%m%d')
                if one_week_ago <= file_date <= today:
                    file_dates.append(file_date_str)
            except ValueError:
                continue
        return sorted(set(file_dates), reverse=True)
    
    # 최근 일주일 내의 파일을 읽어오기 위한 함수
    def get_recent_files(file_prefix):
        files = glob.glob(f"{file_prefix}_*.xlsx")
        recent_files = []
        for file in files:
            file_date_str = file.split('_')[-1].replace('.xlsx', '')
            try:
                file_date = datetime.strptime(file_date_str, '%Y%m%d')
                if one_week_ago <= file_date <= today:
                    recent_files.append(file)
            except ValueError:
                continue
        return sorted(recent_files, reverse=True)
    
    # df_log 파일에서 최근 날짜 목록을 가져오기
    available_dates = get_recent_files_by_date('df_log')
    
    if available_dates:
        # 사용자가 선택한 날짜에 따른 파일 목록 표시
        selected_date = st.selectbox("날짜를 선택하세요", available_dates)
        
        # 선택된 날짜에 해당하는 df_log 파일 읽기
        df_log_files = glob.glob(f"df_log_{selected_date}.xlsx")
        
        if df_log_files:
            st.write(f"선택한 날짜: {selected_date}")
            
            combined_df_log = pd.DataFrame()
            for file_path in df_log_files:
                df = pd.read_excel(file_path, engine='openpyxl')
                combined_df_log = pd.concat([combined_df_log, df], ignore_index=True)
            
            # Check problematic rows
            problematic_rows = combined_df_log[
                (combined_df_log['unique_date'].isnull()) | (combined_df_log['unique_date'] == 1) | (combined_df_log['unique_date'] == 0)
            ]
            
            if not problematic_rows.empty:
                st.warning(f"선택한 날짜({selected_date})에 덜 수집된 사이트 리스트는 아래와 같습니다. 직접 접속 후 확인 필요합니다.")
                st.write("확인해야 할 사이트:")
                # URL 컬럼에 하이퍼링크 추가
                problematic_rows['URL'] = problematic_rows['URL'].apply(lambda x: f'<a href="{x}" target="_blank">{x}</a>')
                # CSS 스타일을 사용하여 특정 열의 너비를 조정합니다.
                st.markdown("""
                    <style>
                        table {
                            width: 100%;
                        }
                        th, td {
                            padding: 5px;
                        }
                        th {
                            text-align: left;
                        }
                        td {
                            max-width: 200px;  /* 기본적으로 열의 최대 폭 설정 */
                            overflow-wrap: break-word;
                        }
                        td:nth-child(1), th:nth-child(1) {  /* unique_date 열 (두 번째 열) */
                            width: 10px;  /* 열의 너비 설정 */
                        }
                        td:nth-child(2), th:nth-child(2) {  /* unique_date 열 (두 번째 열) */
                            width: 20px;  /* 열의 너비 설정 */
                        }
                        td:nth-child(4), th:nth-child(4) {  /* unique_date 열 (두 번째 열) */
                            width: 20px;  /* 열의 너비 설정 */
                        }
                        td:nth-child(5), th:nth-child(5) {  /* max_date 열 (세 번째 열) */
                            width: 20px;  /* 열의 너비 설정 */
                        }
                    </style>
                """, unsafe_allow_html=True)
                
                # 데이터프레임을 HTML로 렌더링
                st.markdown(problematic_rows.to_html(escape=False), unsafe_allow_html=True)
            else:
                st.success(f"선택한 날짜({selected_date})에는 unique_date가 Null이거나 1인 데이터가 없습니다.")
        else:
            st.write(f"선택한 날짜({selected_date})에 해당하는 df_log 파일을 찾을 수 없습니다.")
    else:
        st.write("최근 15일 내에 df_log 파일을 찾을 수 없습니다.")
    
    # df_list 파일 읽기 및 처리
    df_list_file_paths = get_recent_files('df_list')
    if df_list_file_paths:
        combined_df_list = pd.DataFrame()
        
        for file_path in df_list_file_paths:
            df = pd.read_excel(file_path, engine='openpyxl')
            combined_df_list = pd.concat([combined_df_list, df], ignore_index=True)
        
        combined_df_list = combined_df_list.drop_duplicates()
    
        column_order = ['SITE_NO', '출처', '제목', 'URL', '작성일']
        combined_df_list = combined_df_list.reindex(columns=column_order)
    
        combined_df_list['URL'] = combined_df_list['URL'].apply(lambda x: f'<a href="{x}" target="_blank">{x}</a>')
    
        combined_df_list['작성일'] = pd.to_datetime(combined_df_list['작성일'], errors='coerce')
        combined_df_list = combined_df_list.sort_values(by='작성일', ascending=False)
    
        # "df_list 파일" 테이블에 대한 CSS 스타일을 정의합니다.
        st.markdown("""
            <style>
                #df-list-table {
                    width: 100%;
                }
                #df-list-table th, #df-list-table td {
                    padding: 5px;
                }
                #df-list-table th {
                    text-align: left;
                }
                #df-list-table td {
                    max-width: 50px;  /* 열의 최대 폭 설정 */
                    width: 50px;  /* 열의 너비 설정 */
                    overflow-wrap: break-word;
                    word-wrap: break-word;  /* 단어를 잘라서 줄바꿈 */
                }
                #df-list-table td:nth-child(1), #df-list-table th:nth-child(1) {  /* 첫 번째 열 */
                    width: 5px;  /* 첫 번째 열의 너비 설정 */
                    max-width: 5px;  /* 첫 번째 열의 최대 너비 설정 */
                    overflow: hidden;  /* 내용이 넘칠 경우 숨김 */
                }
                #df-list-table td:nth-child(2), #df-list-table th:nth-child(2) {  /* 두 번째 열 */
                    width: 10px;  /* 두 번째 열의 너비 설정 */
                }
                #df-list-table td:nth-child(3), #df-list-table th:nth-child(3) {  /* 두 번째 열 */
                    width: 20px;  /* 두 번째 열의 너비 설정 */
                }
                #df-list-table td:nth-child(5), #df-list-table th:nth-child(5) {  /* 두 번째 열 */
                    width: 10px;  /* 두 번째 열의 너비 설정 */
                    max-width: 10px;  /* 첫 번째 열의 최대 너비 설정 */
                    overflow: hidden;  /* 내용이 넘칠 경우 숨김 */
                }
            </style>
        """, unsafe_allow_html=True)
    
        st.write(f"최근 15일 내에 수집된 공고 파일 {len(df_list_file_paths)}개를 불러왔습니다.")
        st.write("포함 키워드 : 특허, 제안, 심의")
    
        search_keyword = st.text_input("수집된 공고 제목에서 검색할 키워드를 입력하세요")
    
        if search_keyword:
            search_results = combined_df_list[combined_df_list['제목'].str.contains(search_keyword, na=False)]
            st.write(f"'{search_keyword}' 검색 결과:")
            st.markdown(search_results.to_html(escape=False, index=False, table_id="df-list-table"), unsafe_allow_html=True)
        else:
            st.write("df_list 파일의 전체 데이터:")
            st.markdown(combined_df_list.to_html(escape=False, index=False, table_id="df-list-table"), unsafe_allow_html=True)

    else:
        st.write("최근 15일 내에 df_list 파일을 찾을 수 없습니다.")
    


# 메인 실행 흐름
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    login()
else:
    main_app()
