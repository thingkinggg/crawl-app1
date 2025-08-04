import streamlit as st
import pandas as pd
from model_match_agent import ModelMatchAgentAzure
import altair as alt
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_openai import AzureChatOpenAI

def prepare_price_trend_df(df_raw, selected_model, similar_models_df):
    model_list = similar_models_df['Model'].tolist() + [selected_model]
    chart_df = df_raw[df_raw['Model'].isin(model_list)].copy()

    base_brand = chart_df[chart_df['Model'] == selected_model]['BRAND_AD_HOC'].mode().iloc[0]
    chart_df = chart_df[chart_df['BRAND_AD_HOC'] != base_brand]

    chart_df = chart_df[['Model', 'BRAND_AD_HOC', 'yyyymm', 'UNIT']].dropna()
    chart_df['yyyymm'] = chart_df['yyyymm'].astype(str)

    return chart_df


def draw_price_trend_chart(chart_df):
    return alt.Chart(chart_df).mark_line(point=True).encode(
        x=alt.X('yyyymm:O', title='월'),
        y=alt.Y('UNIT:Q', title='단가'),
        color='Model:N',
        tooltip=['Model', 'UNIT', 'yyyymm']
    ).properties(width=700, height=400)


def summarize_price_trend(chart_df, selected_model, similar_models_df, llm):
    sample = chart_df.groupby(['Model', 'yyyymm'])['unit'].mean().reset_index()
    pivot = sample.pivot(index='yyyymm', columns='Model', values='UNIT').fillna('')
    trend_text = pivot.to_string()

    model_names = ", ".join(similar_models_df['Model'].tolist())
    prompt = PromptTemplate.from_template(
        """
        기준 모델: {base_model}
        비교 모델: {similar_models}

        각 모델의 월별 가격 추이:
        {trend_table}

        위 가격 변화로부터 얻을 수 있는 마케팅 인사이트를 3줄 이내로 요약해줘.
        """
    )

    chain = LLMChain(llm=llm, prompt=prompt)
    return chain.run(base_model=selected_model, similar_models=model_names, trend_table=trend_text)


# Azure OpenAI 설정
AZURE_OPENAI_KEY = st.secrets["AZURE_OPENAI_KEY"]
AZURE_ENDPOINT = st.secrets["AZURE_ENDPOINT"]
DEPLOYMENT_NAME = st.secrets["DEPLOYMENT_NAME"]

st.title("🧠 경쟁 모델 매칭 AI Agent")
st.markdown("""
- 매출 데이터(.xlsx)를 업로드하면,
- 특정 모델명을 기준으로 **경쟁 브랜드 유사 모델**을 추천하고,
- **추천 이유 + 가격 변화 추이 + 가격 해석 요약**까지 제공합니다.
""")

# 파일 업로드
uploaded_file = st.file_uploader("📁 매출 데이터 (.xlsx) 업로드", type=["xlsx"])

if uploaded_file:
    df_raw = pd.read_excel(uploaded_file)
    st.success(f"✅ 데이터 업로드 완료! 총 {len(df_raw)}행")

    model_name = st.selectbox("🔍 기준 모델 (ORIG_MODEL)", sorted(df_raw['ORIG_MODEL'].unique()))

    if st.button("🔎 유사 경쟁 모델 찾기"):
        with st.spinner("AI 분석 중..."):
            try:
                agent = ModelMatchAgentAzure(
                    df_raw=df_raw,
                    openai_api_key=AZURE_OPENAI_KEY,
                    endpoint=AZURE_ENDPOINT,
                    deployment_name=DEPLOYMENT_NAME
                )
                similar_models, explanation = agent.explain_recommendation(model_name)

                if isinstance(similar_models, str):
                    st.warning(similar_models)
                else:
                    st.subheader("📋 유사 경쟁 모델 추천 결과")
                    st.dataframe(similar_models)

                    st.subheader("💡 추천 이유 (LLM 기반 요약)")
                    st.write(explanation)

                    st.subheader("📈 경쟁 모델의 월별 가격 변화 추이")
                    chart_df = prepare_price_trend_df(df_raw, model_name, similar_models)
                    st.altair_chart(draw_price_trend_chart(chart_df), use_container_width=True)

                    st.subheader("🧠 가격 추이 요약 분석 (LLM)")
                    with st.spinner("LLM이 가격 트렌드를 분석 중입니다..."):
                        price_summary = summarize_price_trend(chart_df, model_name, similar_models, agent.llm)
                        st.write(price_summary)

            except Exception as e:
                st.error(f"[오류] 모델 분석 중 문제가 발생했습니다: {e}")


