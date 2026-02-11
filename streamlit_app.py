import streamlit as st
import pandas as pd
import plotly.express as px
import bar_chart_race as bcr
import tempfile
import os
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# --- [폰트 설정] 한글 깨짐 방지 ---
# Windows: 'Malgun Gothic', Mac: 'AppleGothic'
# 아래 코드는 시스템에서 한글 폰트를 찾아 자동으로 설정하려 시도합니다.
def set_korean_font():
    try:
        if os.name == 'nt': # Windows
            plt.rc('font', family='Malgun Gothic')
        else: # Mac/Linux
            plt.rc('font', family='AppleGothic')
        plt.rcParams['axes.unicode_minus'] = False # 마이너스 기호 깨짐 방지
    except:
        pass

st.set_page_config(page_title="실적 바 차트 레이스", layout="wide")

st.title("📊 부서별 실적 애니메이션 차트")
st.info("웹 환경에서는 Plotly로 즉시 확인하고, 발표용은 하단에서 GIF로 추출하세요.")

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

        required_cols = ['년도', '부서', '실적']
        if all(col in df.columns for col in required_cols):
            
            # --- [기능 1] Plotly 애니메이션 차트 (기존 양식 유지) ---
            st.divider()
            st.subheader("📈 인터랙티브 차트 (웹 확인용)")
            
            fig = px.bar(
                df, 
                x="실적", 
                y="부서", 
                color="부서", 
                animation_frame="년도", 
                animation_group="부서",
                orientation='h',
                range_x=[0, df['실적'].max() * 1.2], 
                title="연도별 부서 실적 변화",
                text="실적"
            )

            fig.update_layout(
                yaxis={'categoryorder':'total ascending'},
                margin=dict(l=50, r=50, t=80, b=50),
                height=600,
                showlegend=False
            )
            
            fig.layout.updatemenus[0].buttons[0].args[1]['frame']['duration'] = 1000
            fig.layout.updatemenus[0].buttons[0].args[1]['transition']['duration'] = 500

            st.plotly_chart(fig, use_container_width=True)
            st.success("왼쪽 하단의 Play(▶) 버튼을 클릭해 보세요!")

            # --- [기능 2] GIF 생성 및 다운로드 (추가된 부분) ---
            st.divider()
            st.subheader("🎞️ PPT 삽입용 GIF 다운로드")
            st.warning("GIF 생성 시 한글 폰트 적용을 위해 잠시만 기다려주세요 (FFmpeg 설치 필요)")

            if st.button("🚀 GIF 애니메이션 파일 만들기"):
                with st.spinner('데이터를 변환하고 GIF를 생성 중입니다...'):
                    try:
                        set_korean_font() # 한글 폰트 적용
                        
                        # 데이터 피벗 (년도 index, 부서 columns, 실적 values)
                        df_pivot = df.pivot(index='년도', columns='부서', values='실적').fillna(0)
                        
                        # 임시 파일 생성 (NamedTemporaryFile - 오타 수정 완료)
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.gif') as tmp:
                            bcr.bar_chart_race(
                                df=df_pivot,
                                filename=tmp.name,
                                title='연도별 부서 실적 변화',
                                orientation='h',
                                sort='desc',
                                n_bars=10,
                                steps_per_period=15, # 숫자가 높을수록 부드럽지만 오래 걸림
                                period_length=1000,   # 프레임 전환 속도
                                cmap='viridis'        # 컬러 테마
                            )
                            
                            with open(tmp.name, 'rb') as f:
                                gif_bytes = f.read()
                            
                            st.image(gif_bytes, caption="생성된 GIF 미리보기")
                            
                            st.download_button(
                                label="💾 GIF 파일 다운로드",
                                data=gif_bytes,
                                file_name="performance_race.gif",
                                mime="image/gif"
                            )
                        
                        os.remove(tmp.name) # 임시 파일 삭제
                        
                    except Exception as e:
                        st.error(f"GIF 생성 중 오류가 발생했습니다: {e}")
                        st.info("Tip: 시스템에 FFmpeg가 설치되어 있는지 확인해 주세요.")
            
        else:
            st.error(f"엑셀 파일에 {required_cols} 열이 포함되어 있어야 합니다.")
            
    except Exception as e:
        st.error(f"파일을 읽는 중 오류가 발생했습니다: {e}")
