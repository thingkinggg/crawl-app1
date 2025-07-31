import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
import faiss
from langchain_openai import AzureChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

class ModelMatchAgentAzure:
    def __init__(self, df_raw: pd.DataFrame, openai_api_key: str, endpoint: str, deployment_name: str):
        self.raw_df = df_raw
        self.api_key = openai_api_key
        self.endpoint = endpoint
        self.deployment_name = deployment_name

        self.df = self._build_representative_df()
        self._preprocess()
        self._build_vector_db()

        self.llm = AzureChatOpenAI(
            openai_api_key=self.api_key,
            azure_endpoint=self.endpoint,
            deployment_name=self.deployment_name,
            api_version="2024-02-01",
            temperature=0
        )

    def _build_representative_df(self):
        return (
            self.raw_df.groupby('ORIG_MODEL')
            .agg({
                '44_Capacity': 'mean',
                '54_전압_V': lambda x: x.mode().iloc[0] if not x.mode().empty else None,
                '38_Energy': lambda x: x.mode().iloc[0] if not x.mode().empty else None,
                '35_Color': lambda x: x.mode().iloc[0] if not x.mode().empty else None,
                'MAIN_TYPE': lambda x: x.mode().iloc[0] if not x.mode().empty else None,
                '48_Dispenser': lambda x: x.mode().iloc[0] if not x.mode().empty else None,
                '50_ICE_Manual/Dispenser/Automatic': lambda x: x.mode().iloc[0] if not x.mode().empty else None,
                '51_ICE_Type(Cube/Crushed/Cabinet)': lambda x: x.mode().iloc[0] if not x.mode().empty else None,
                '52_wifi': lambda x: x.mode().iloc[0] if not x.mode().empty else None,
                '53_smart': lambda x: x.mode().iloc[0] if not x.mode().empty else None,
                '55_Standard/Countertop(D)': lambda x: x.mode().iloc[0] if not x.mode().empty else None,
                'BRAND_AD_HOC': lambda x: x.mode().iloc[0],
                'Model': lambda x: x.mode().iloc[0],
            })
            .reset_index()
        )

    def _preprocess(self):
        df_specs = self.df.copy()

        # 전압 수치화
        df_specs['54_전압_V'] = df_specs['54_전압_V'].replace({
            '110V': 110, '220V': 220, '110V/220V': 165,
            '127V': 127, '127V/220V': 173.5
        })
        df_specs['54_전압_V'] = pd.to_numeric(df_specs['54_전압_V'], errors='coerce').fillna(0)

        # 범주형 수치화
        binary_cols = ['48_Dispenser', '50_ICE_Manual/Dispenser/Automatic',
                       '51_ICE_Type(Cube/Crushed/Cabinet)', '52_wifi', '53_smart']
        for col in binary_cols:
            df_specs[col] = df_specs[col].replace({'Y': 1, 'N': 0, '-': 0})
            df_specs[col] = pd.to_numeric(df_specs[col], errors='coerce').fillna(0)

        # 등급 인코딩
        grade_map = {'A+++': 3, 'A++': 2, 'A+': 1, 'A': 0, 'B': -1, 'C': -2}
        df_specs['38_Energy'] = df_specs['38_Energy'].map(grade_map).fillna(0)

        # 용량
        df_specs['44_Capacity'] = pd.to_numeric(df_specs['44_Capacity'], errors='coerce').fillna(0)

        # 범주형 → One-Hot
        df_specs = pd.get_dummies(df_specs, columns=[
            'MAIN_TYPE', '35_Color', '55_Standard/Countertop(D)'
        ], prefix=['MT', 'Color', 'STD'])

        self.df_specs_raw = df_specs
        self.scaler = StandardScaler()
        self.specs_scaled = self.scaler.fit_transform(
            df_specs.drop(columns=['ORIG_MODEL', 'Model', 'BRAND_AD_HOC'])
        )

    def _build_vector_db(self):
        dim = self.specs_scaled.shape[1]
        self.index = faiss.IndexFlatL2(dim)
        self.index.add(self.specs_scaled)

    def search_similar_models(self, model_name: str, top_n=5):
        idx = self.df[self.df['ORIG_MODEL'] == model_name].index
        if len(idx) == 0:
            return f"[에러] 모델 '{model_name}'을 찾을 수 없습니다."
        
        idx = idx[0]
        query_vector = self.specs_scaled[idx].reshape(1, -1)
        base_brand = self.df.loc[idx, 'BRAND_AD_HOC']

        distances, indices = self.index.search(query_vector, 30)

        filtered_indices = []
        filtered_distances = []
        for dist, i in zip(distances[0], indices[0]):
            if i == idx:
                continue
            if self.df.loc[i, 'BRAND_AD_HOC'] != base_brand:
                filtered_indices.append(i)
                filtered_distances.append(dist)
            if len(filtered_indices) >= top_n:
                break

        if not filtered_indices:
            return f"[안내] '{base_brand}' 브랜드 외 유사 모델이 없습니다."

        results = self.df.iloc[filtered_indices][[
            'Model', 'BRAND_AD_HOC', 'MAIN_TYPE',
            '35_Color', '38_Energy', '44_Capacity', '55_Standard/Countertop(D)'
        ]].copy()
        results['distance'] = filtered_distances
        return results

    def explain_recommendation(self, model_name: str, top_n=5):
        similar_models = self.search_similar_models(model_name, top_n)
        if isinstance(similar_models, str):
            return similar_models, None

        models_list = "\n".join([
            f"- ({row.BRAND_AD_HOC}, {row.MAIN_TYPE}, {row['44_Capacity']}L, {row['38_Energy']})"
            for _, row in similar_models.iterrows()
        ])

        prompt = PromptTemplate.from_template(
            "기준 모델: {model}\n"
            "유사한 모델:\n{models_list}\n\n"
            "기준 모델과 경쟁사 브랜드의 유사한 모델들이 왜 비슷한지 주요 스펙 기준으로 요약해줘. (3줄 이내)"
        )

        chain = LLMChain(llm=self.llm, prompt=prompt)
        response = chain.run(model=model_name, models_list=models_list)
        return similar_models, response
