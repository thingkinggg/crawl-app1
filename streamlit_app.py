import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="실적 바 차트 레이스",
    page_icon="📊",
    layout="wide"
)

st.title("📊 부서별 실적 애니메이션 차트")
st.caption("업로드한 데이터로 연도별 부서 실적 변화를 레이스 바 차트로 시각화합니다.")

# --- Sidebar controls ---
st.sidebar.header("⚙️ 시각화 설정")
top_n = st.sidebar.slider("표시할 Top N 부서", min_value=3, max_value=30, value=10, step=1)
frame_ms = st.sidebar.slider("프레임 재생 속도(ms)", min_value=200, max_value=2000, value=900, step=100)
transition_ms = st.sidebar.slider("전환(transition) 속도(ms)", min_value=0, max_value=1500, value=350, step=50)

uploaded_file = st.file_uploader("엑셀 또는 CSV 파일을 업로드하세요", type=["xlsx", "csv"])

if uploaded_file:
    try:
        # --- Load ---
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        st.subheader("📌 데이터 미리보기")
        st.dataframe(df.head(), use_container_width=True)

        required_cols = ["년도", "부서", "실적"]
        if not all(c in df.columns for c in required_cols):
            st.error(f"필수 컬럼이 필요합니다: {required_cols}")
            st.stop()

        # --- Clean / types ---
        df = df[required_cols].copy()
        df["실적"] = pd.to_numeric(df["실적"], errors="coerce")
        df = df.dropna(subset=["년도", "부서", "실적"])

        # 연도 정렬 안정화: 숫자/문자 섞여도 순서가 안 꼬이도록
        df["년도"] = df["년도"].astype(str)

        # --- Top N per year (race 느낌 강화) ---
        df_top = (
            df.sort_values(["년도", "실적"], ascending=[True, False])
              .groupby("년도", as_index=False)
              .head(top_n)
        )

        # 색상 고정 매핑(프레임 바뀌어도 부서 색 유지)
        depts = sorted(df_top["부서"].unique().tolist())
        palette = px.colors.qualitative.Set2  # 깔끔한 계열
        color_map = {d: palette[i % len(palette)] for i, d in enumerate(depts)}

        # x축 범위 고정(프레임마다 흔들리지 않게)
        x_max = df_top["실적"].max() * 1.15

        # y축 순서(전체 최대 실적 기준으로 “일관된” 정렬)
        # 완전한 frame별 재정렬 레이스는 plotly frames로 커스텀해야 하지만,
        # 이 방식만으로도 시각적 안정감이 크게 좋아집니다.
        overall_order = (
            df_top.groupby("부서")["실적"].max()
                 .sort_values(ascending=True)
                 .index.tolist()
        )

        # --- Plot ---
        fig = px.bar(
            df_top,
            x="실적",
            y="부서",
            color="부서",
            color_discrete_map=color_map,
            animation_frame="년도",
            animation_group="부서",
            orientation="h",
            range_x=[0, x_max],
            text="실적",
            title="연도별 부서 실적 변화 (Race Bar)"
        )

        # 라벨/호버/트레이스
        fig.update_traces(
            texttemplate="%{x:,.0f}",
            textposition="outside",
            cliponaxis=False,
            hovertemplate=(
                "<b>%{y}</b><br>"
                "실적: %{x:,.0f}<extra></extra>"
            )
        )

        # 레이아웃(가독성 업)
        dynamic_height = max(480, 42 * len(df_top["부서"].unique()) + 140)
        fig.update_layout(
            template="plotly_white",
            height=dynamic_height,
            margin=dict(l=80, r=40, t=80, b=40),
            showlegend=False,
            bargap=0.18,
            title=dict(x=0.01, y=0.98),
            xaxis=dict(
                title="",
                tickformat=",",
                showgrid=True,
                gridcolor="rgba(0,0,0,0.06)",
                zeroline=False
            ),
            yaxis=dict(
                title="",
                categoryorder="array",
                categoryarray=overall_order,
                tickfont=dict(size=13)
            )
        )

        # 애니메이션 속도 조절 + 슬라이더 표시 개선
        if fig.layout.updatemenus and len(fig.layout.updatemenus) > 0:
            fig.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = frame_ms
            fig.layout.updatemenus[0].buttons[0].args[1]["transition"]["duration"] = transition_ms

        if fig.layout.sliders and len(fig.layout.sliders) > 0:
            fig.layout.sliders[0].currentvalue.prefix = "년도: "
            fig.layout.sliders[0].currentvalue.font.size = 14

        st.plotly_chart(
            fig,
            use_container_width=True,
            config={
                "displayModeBar": False,     # 상단 툴바 숨겨서 더 깔끔하게
                "scrollZoom": False
            }
        )

        st.success("왼쪽 하단의 Play(▶) 버튼을 눌러보세요. Top N / 속도도 사이드바에서 조절 가능합니다.")

    except Exception as e:
        st.error(f"파일을 읽는 중 오류가 발생했습니다: {e}")
