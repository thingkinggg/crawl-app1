import streamlit as st
import pandas as pd
from model_match_agent import ModelMatchAgentAzure  # 별도 모듈로 분리된 클래스
import os

# ------------------------
# Streamlit UI Layout
# ------------------------
st.set_page_config(page_title="Model Match AI Agent", layout="wide")
st.title("🔍 경쟁 모델 추천 에이전트")
st.markdown("고객이 업로드한 매출 데이터 기반으로 유사한 **경쟁 브랜드 모델**을 추천하고, AI가 추천 이유를 요약해줍니다.")

# ------------------------
# Sidebar Inputs
# ------------------------
st.sidebar.header("🧾 설정")
openai_key = st.sidebar.text_input("Azure OpenAI Key", type="password")
endpoint = st.sidebar.text_input("Azure OpenAI Endpoint", value="https://<your-resource>.openai.azure.com/")
deployment_name = st.sidebar.text_input("Deployment Name", value="gpt-4o")

# ------------------------
# File Upload
# ------------------------
st.subheader("1. 매출 데이터 업로드")
uploaded_file = st.file_uploader("엑셀 파일(.xlsx) 업로드", type=["xlsx"])

if uploaded_file and openai_key:
    try:
        df_raw = pd.read_excel(uploaded_file)

        # 모델 초기화
        agent = ModelMatchAgentAzure(
            df_raw=df_raw,
            openai_api_key=openai_key,
            endpoint=endpoint,
            deployment_name=deployment_name
        )

        st.success("✅ 데이터 로딩 및 벡터 구축 완료")

        # ------------------------
        # 모델 입력 UI
        # ------------------------
        st.subheader("2. 모델명을 입력하면 유사 경쟁 모델을 추천합니다")
        model_list = agent.df['ORIG_MODEL'].unique().tolist()
        selected_model = st.selectbox("기준 모델을 선택하세요", options=model_list)
        top_n = st.slider("추천 개수", 1, 10, 5)

        if st.button("🔍 유사 경쟁 모델 찾기"):
            similar_models, explanation = agent.explain_recommendation(selected_model, top_n=top_n)

            if isinstance(similar_models, str):
                st.warning(similar_models)
            else:
                st.write("### 🔁 유사 경쟁 모델 리스트")
                st.dataframe(similar_models, use_container_width=True)
                
                if explanation:
                    st.markdown("### 🧠 추천 이유 (AI 요약)")
                    st.info(explanation)

        # ------------------------
        # 추가 기능
        # ------------------------
        st.subheader("3. 🔧 추가 기능")
        with st.expander("📊 전체 모델 분포 보기"):
            st.bar_chart(df_raw['ORIG_MODEL'].value_counts())

        with st.expander("📥 데이터 미리보기"):
            st.dataframe(df_raw.head(), use_container_width=True)

    except Exception as e:
        st.error(f"❌ 오류 발생: {e}")

else:
    st.info("⬆️ 먼저 OpenAI 인증 정보와 데이터를 업로드하세요")
