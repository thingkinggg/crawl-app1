import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

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

       # =========================
        # (선택) 동일 (년도,부서) 중복행이 있으면 합산
        # =========================
        df_viz = df[required_cols].copy()
        df_viz["실적"] = pd.to_numeric(df_viz["실적"], errors="coerce")
        df_viz = df_viz.dropna(subset=["년도", "부서", "실적"])
        df_viz["년도"] = df_viz["년도"].astype(str)
        
        df_viz = (
            df_viz.groupby(["년도", "부서"], as_index=False)["실적"].sum()
        )
        
        # =========================
        # Top N (레이스 핵심) + 축 범위 고정용
        # =========================
        TOP_N = 10  # 원하면 sidebar slider로 바꿔도 됨
        df_sorted = df_viz.sort_values(["년도", "실적"], ascending=[True, False])
        df_top_all = df_sorted.groupby("년도", as_index=False).head(TOP_N)
        
        x_max = df_top_all["실적"].max() * 1.15
        
        # 연도 정렬 안정화(숫자 연도면 숫자 기준 정렬, 아니면 문자열 정렬)
        year_key = pd.to_numeric(df_top_all["년도"], errors="coerce")
        if year_key.notna().any():
            years = (
                df_top_all.assign(_k=pd.to_numeric(df_top_all["년도"], errors="coerce"))
                         .sort_values("_k")["년도"].unique().tolist()
            )
        else:
            years = sorted(df_top_all["년도"].unique().tolist())
        
        # =========================
        # 부서별 색상 고정(프레임 바뀌어도 동일 부서=동일 색)
        # =========================
        depts_all = sorted(df_viz["부서"].unique().tolist())
        palette = px.colors.qualitative.Set2
        color_map = {d: palette[i % len(palette)] for i, d in enumerate(depts_all)}
        
        def frame_data_for_year(y):
            d = df_viz[df_viz["년도"] == y].nlargest(TOP_N, "실적").copy()
            # y축은 아래->위 순서가 categoryarray 순서라서 (낮은 실적 -> 높은 실적)로 정렬하면
            # 최고 실적이 맨 위로 올라감
            d = d.sort_values("실적", ascending=True)
        
            depts = d["부서"].tolist()
            vals = d["실적"].tolist()
            colors = [color_map[x] for x in depts]
            return d, depts, vals, colors
        
        # 첫 프레임(초기 화면)
        d0, depts0, vals0, colors0 = frame_data_for_year(years[0])
        
        fig = go.Figure(
            data=[
                go.Bar(
                    x=vals0,
                    y=depts0,
                    orientation="h",
                    marker=dict(color=colors0),
                    text=[f"{v:,.0f}" for v in vals0],
                    textposition="outside",
                    cliponaxis=False,
                    # object constancy(부서 단위로 트래킹) → 순위 변동 시 위/아래 이동이 매끄러움
                    ids=depts0,
                    hovertemplate="<b>%{y}</b><br>실적: %{x:,.0f}<extra></extra>",
                )
            ],
            layout=go.Layout(
                template="plotly_white",
                height=max(520, 44 * TOP_N + 220),
                margin=dict(l=90, r=40, t=90, b=40),
                showlegend=False,
                xaxis=dict(range=[0, x_max], tickformat=",", showgrid=True, gridcolor="rgba(0,0,0,0.06)", zeroline=False, title=""),
                yaxis=dict(
                    title="",
                    categoryorder="array",
                    categoryarray=depts0,  # 첫 프레임 순서
                    tickfont=dict(size=13)
                ),
                title=dict(text=f"연도별 부서 실적 변화 (Race Bar) — {years[0]}", x=0.01, y=0.98),
                annotations=[
                    dict(
                        text=str(years[0]),
                        x=0.99, y=1.12, xref="paper", yref="paper",
                        showarrow=False,
                        font=dict(size=34, color="rgba(0,0,0,0.25)"),
                        xanchor="right"
                    )
                ],
                updatemenus=[
                    dict(
                        type="buttons",
                        direction="left",
                        x=0.01, y=-0.12,
                        showactive=False,
                        buttons=[
                            dict(
                                label="▶ Play",
                                method="animate",
                                args=[
                                    None,
                                    dict(
                                        frame=dict(duration=900, redraw=True),   # 필요시 조절
                                        transition=dict(duration=350),
                                        fromcurrent=True,
                                        mode="immediate",
                                    )
                                ],
                            ),
                            dict(
                                label="⏸ Pause",
                                method="animate",
                                args=[[None], dict(frame=dict(duration=0, redraw=False), mode="immediate")],
                            ),
                        ],
                    )
                ],
                sliders=[
                    dict(
                        x=0.01, y=-0.05,
                        len=0.98,
                        currentvalue=dict(prefix="년도: ", font=dict(size=14)),
                        pad=dict(b=0, t=30),
                        steps=[]
                    )
                ],
            )
        )
        
        # 프레임 생성 + 슬라이더 스텝 생성
        frames = []
        slider_steps = []
        for y in years:
            d, depts, vals, colors = frame_data_for_year(y)
        
            frames.append(
                go.Frame(
                    name=str(y),
                    data=[
                        go.Bar(
                            x=vals,
                            y=depts,
                            orientation="h",
                            marker=dict(color=colors),
                            text=[f"{v:,.0f}" for v in vals],
                            textposition="outside",
                            cliponaxis=False,
                            ids=depts,
                            hovertemplate="<b>%{y}</b><br>실적: %{x:,.0f}<extra></extra>",
                        )
                    ],
                    layout=go.Layout(
                        yaxis=dict(categoryorder="array", categoryarray=depts),
                        title=dict(text=f"연도별 부서 실적 변화 (Race Bar) — {y}", x=0.01, y=0.98),
                        annotations=[
                            dict(
                                text=str(y),
                                x=0.99, y=1.12, xref="paper", yref="paper",
                                showarrow=False,
                                font=dict(size=34, color="rgba(0,0,0,0.25)"),
                                xanchor="right"
                            )
                        ]
                    )
                )
            )
        
            slider_steps.append(
                dict(
                    method="animate",
                    label=str(y),
                    args=[
                        [str(y)],
                        dict(frame=dict(duration=0, redraw=True), transition=dict(duration=0), mode="immediate")
                    ],
                )
            )
        
        fig.frames = frames
        fig.layout.sliders[0].steps = slider_steps
        
        # 출력
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
                st.success("왼쪽 하단의 Play(▶) 버튼을 눌러보세요. Top N / 속도도 사이드바에서 조절 가능합니다.")
        
            except Exception as e:
                st.error(f"파일을 읽는 중 오류가 발생했습니다: {e}")
