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
