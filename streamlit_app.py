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

        # 데이터 가공 (년도별로 정렬되어 있어야 애니메이션이 순서대로 나옵니다)
        df = df.sort_values('년도')

        try:
            # 피벗 테이블 생성
            df_pivot = df.pivot(index='년도', columns='부서', values='실적').fillna(0)
            
            st.subheader("🎬 애니메이션 생성")
            st.info("GIF 생성은 데이터 양에 따라 10~30초 정도 소요될 수 있습니다.")
            
            if st.button("🚀 GIF 애니메이션 생성 및 다운로드 준비"):
                with st.spinner('차트 프레임을 생성하고 GIF로 굽는 중...'):
                    # 임시 파일 경로 설정 (NamedTemporaryFile로 수정)
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.gif') as tmp:
                        # bar_chart_race 실행
                        bcr.bar_chart_race(
                            df=df_pivot,
                            filename=tmp.name, # 임시 경로에 저장
                            title='연도별 부서 실적 변화',
                            orientation='h',
                            sort='desc',
                            n_bars=10,
                            fixed_max=True,
                            steps_per_period=10, # 프레임 부드러움 조절
                            period_length=500    # 한 장면당 시간(ms)
                        )
                        
                        # 생성된 파일 읽기
                        with open(tmp.name, 'rb') as f:
                            gif_bytes = f.read()
                        
                        # 화면에 결과 표시
                        st.image(gif_bytes)
                        
                        # 다운로드 버튼
                        st.download_button(
                            label="💾 생성 완료! GIF 다운로드 받기",
                            data=gif_bytes,
                            file_name="performance_race.gif",
                            mime="image/gif"
                        )
                
                # 작업 완료 후 임시 파일 삭제
                os.remove(tmp.name)

        except Exception as e:
            st.error(f"데이터 처리 중 오류 발생: {e}")
            st.warning("데이터에 '년도', '부서', '실적' 컬럼이 있고, 중복된 년도/부서 데이터가 없는지 확인하세요.")
            
    except Exception as e:
        st.error(f"파일을 읽는 중 오류가 발생했습니다: {e}")
