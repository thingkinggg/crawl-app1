import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image
import io
import tempfile
import os

st.set_page_config(page_title="실적 바 차트 레이스", layout="wide")
st.title("📊 부서별 실적 애니메이션 차트")
st.info("이 라이브러리는 ffmpeg 설치 없이도 매끄럽게 작동합니다.")

# 1. 파일 업로드
uploaded_file = st.file_uploader("엑셀 또는 CSV 파일을 업로드하세요", type=["xlsx", "csv"])

if uploaded_file:
    # 파일 읽기
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        st.subheader("📌 데이터 미리보기")
        st.dataframe(df.head())
        
        # 필수 열 확인
        required_cols = ['년도', '부서', '실적']
        if all(col in df.columns for col in required_cols):
            
            # 2. Plotly 애니메이션 차트 생성
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
            
            # 레이아웃 디테일 설정
            fig.update_layout(
                yaxis={'categoryorder':'total ascending'},
                margin=dict(l=50, r=50, t=80, b=50),
                height=600,
                showlegend=False
            )
            
            # 애니메이션 속도 조절
            fig.layout.updatemenus[0].buttons[0].args[1]['frame']['duration'] = 1000
            fig.layout.updatemenus[0].buttons[0].args[1]['transition']['duration'] = 500
            
            # 3. 화면에 출력
            st.plotly_chart(fig, use_container_width=True)
            st.success("왼쪽 하단의 Play(▶) 버튼을 클릭해 보세요!")
            
            # 4. GIF 다운로드 기능 (Kaleido 대신 matplotlib 사용)
            st.markdown("---")
            st.subheader("🎬 GIF 파일로 다운로드")
            
            col1, col2 = st.columns([1, 3])
            with col1:
                frame_duration = st.slider("프레임 속도 (ms)", 500, 2000, 1000, 100)
            
            if st.button("📥 GIF 생성 및 다운로드", type="primary"):
                with st.spinner("GIF 파일을 생성하는 중입니다... (수초 소요)"):
                    try:
                        import matplotlib.pyplot as plt
                        import matplotlib
                        matplotlib.use('Agg')
                        
                        frames = []
                        years = sorted(df['년도'].unique())
                        
                        for year in years:
                            # 해당 년도 데이터
                            df_year = df[df['년도'] == year].copy()
                            df_year = df_year.sort_values('실적')
                            
                            # Matplotlib로 차트 생성
                            fig_mpl, ax = plt.subplots(figsize=(12, 6))
                            
                            bars = ax.barh(df_year['부서'], df_year['실적'], 
                                          color=plt.cm.Set3(range(len(df_year))))
                            
                            # 막대 끝에 수치 표시
                            for i, (idx, row) in enumerate(df_year.iterrows()):
                                ax.text(row['실적'], i, f" {row['실적']:,}", 
                                       va='center', fontsize=10)
                            
                            ax.set_xlim(0, df['실적'].max() * 1.2)
                            ax.set_xlabel('실적', fontsize=12)
                            ax.set_title(f'연도별 부서 실적 변화 - {year}년', 
                                        fontsize=14, fontweight='bold')
                            ax.grid(axis='x', alpha=0.3)
                            
                            plt.tight_layout()
                            
                            # 이미지로 변환
                            buf = io.BytesIO()
                            plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
                            buf.seek(0)
                            img = Image.open(buf)
                            frames.append(img)
                            plt.close()
                        
                        # GIF 생성
                        gif_buffer = io.BytesIO()
                        frames[0].save(
                            gif_buffer,
                            format='GIF',
                            save_all=True,
                            append_images=frames[1:],
                            duration=frame_duration,
                            loop=0
                        )
                        gif_buffer.seek(0)
                        
                        # 다운로드 버튼
                        st.download_button(
                            label="💾 GIF 파일 저장",
                            data=gif_buffer,
                            file_name="부서별_실적_애니메이션.gif",
                            mime="image/gif"
                        )
                        
                        st.success("✅ GIF 파일이 준비되었습니다! 위 버튼을 클릭하여 다운로드하세요.")
                        
                        # 미리보기
                        st.image(gif_buffer, caption="생성된 GIF 미리보기")
                        
                    except ImportError:
                        st.error("matplotlib 패키지가 필요합니다.")
                        st.code("pip install matplotlib pillow", language="bash")
                    except Exception as e:
                        st.error(f"GIF 생성 중 오류가 발생했습니다: {e}")
            
            st.info("💡 GIF 파일은 PPT, 이메일, 웹사이트 등 어디서든 사용할 수 있습니다!")
            
        else:
            st.error(f"엑셀 파일에 {required_cols} 열이 포함되어 있어야 합니다.")
            
    except Exception as e:
        st.error(f"파일을 읽는 중 오류가 발생했습니다: {e}")
