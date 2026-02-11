import streamlit as st
import pandas as pd
import bar_chart_race as bcr
import tempfile
import os

st.set_page_config(page_title="실적 바 차트 레이스", layout="wide")

st.title("📊 부서별 실적 애니메이션 차트")

# 1. 파일 업로드
uploaded_file = st.file_uploader("엑셀 또는 CSV 파일을 업로드하세요", type=["xlsx", "csv"])

if uploaded_file:
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        st.subheader("📌 데이터 미리보기")
        st.dataframe(df.head())

        # 데이터 가공 (bar_chart_race 형식에 맞게 변환)
        # 년도가 인덱스, 부서가 컬럼, 실적이 값인 피벗 테이블이 필요합니다.
        try:
            df_pivot = df.pivot(index='년도', columns='부서', values='실적').fillna(0)
            
            st.subheader("🎬 애니메이션 미리보기 & GIF 저장")
            
            if st.button("🚀 GIF 애니메이션 생성 시작 (시간이 다소 소요될 수 있습니다)"):
                with st.spinner('차트를 생성 중입니다... 잠시만 기다려주세요.'):
                    # 임시 파일 경로 설정
                    with tempfile.NamedTemporaryHeader(delete=False, suffix='.gif') as tmp:
                        # bar_chart_race 실행
                        bcr.bar_chart_race(
                            df=df_pivot,
                            filename=tmp.name,
                            title='연도별 부서 실적 변화',
                            orientation='h',
                            sort='desc',
                            n_bars=10,
                            fixed_max=True,
                            steps_per_period=10,
                            period_length=500
                        )
                        
                        # 생성된 파일 읽기
                        with open(tmp.name, 'rb') as f:
                            gif_bytes = f.read()
                        
                        # 화면에 GIF 표시
                        st.image(gif_bytes)
                        
                        # 다운로드 버튼 생성
                        st.download_button(
                            label="💾 GIF 파일 다운로드 받기",
                            data=gif_bytes,
                            file_name="performance_race.gif",
                            mime="image/gif"
                        )
                
                # 임시 파일 삭제
                os.remove(tmp.name)

        except Exception as e:
            st.error(f"데이터 피벗 중 오류 발생: {e}. 데이터 형식을 확인해주세요 (년도, 부서, 실적 열 필수).")
            
    except Exception as e:
        st.error(f"파일을 읽는 중 오류가 발생했습니다: {e}")
