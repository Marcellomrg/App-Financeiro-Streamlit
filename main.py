
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Finanças",page_icon="💰")
st.markdown("""
# Boas Vindas!
## Nosso APP Financeiro!
Espero que voce curta a experiencia da nossa solucao para organizacao financeira.   
               
""")

file_upload = st.file_uploader(label="Faça o upload aqui: ",type=["csv"])

if file_upload:

    df = pd.read_csv(file_upload)
    df["Data"] = pd.to_datetime(df["Data"],format="%d/%m/%Y").dt.date

    exp1 = st.expander("Dados brutos")

    columns_fmt = {"Valor":st.column_config.NumberColumn("Valor",format="R$ %f")} 
    exp1.dataframe(df,hide_index=True,column_config=columns_fmt)

    exp2 = st.expander("Instituição")
    
    tab_data,tab_history,tab_share = exp2.tabs(["Dados","Histórico","Distribuição"])
    df_instituicao = df.pivot_table(index="Data",columns="Instituição",values="Valor")

    with tab_data:
        st.dataframe(df_instituicao)
    with tab_history:
        st.line_chart(df_instituicao)
    with tab_share:
        data = st.selectbox(label="Selecione uma data",options=df_instituicao.index)
        st.bar_chart(df_instituicao.loc[data])