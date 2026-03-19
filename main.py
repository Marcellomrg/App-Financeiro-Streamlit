# %%
import streamlit as st
import pandas as pd
import requests
import datetime

def get_selic():
    url = "https://www.bcb.gov.br/api/servico/sitebcb/historicotaxasjuros"
    resp = requests.get(url=url)
    df = pd.DataFrame(resp.json()['conteudo'])
    df['DataInicioVigencia'] = pd.to_datetime(df['DataInicioVigencia']).dt.date
    df['DataFimVigencia'] = pd.to_datetime(df['DataFimVigencia']).dt.date.fillna(datetime.datetime.today().date())
    return df

# %%
def stats_geral(df:pd.DataFrame):
        
    df_stats = df.groupby(by="Data")[["Valor"]].sum()
    df_stats['leg'] = df_stats["Valor"].shift(1)
    df_stats['diff mensal Abs.'] = df_stats["Valor"] - df_stats['leg']
    df_stats["Media Diff em 6M"] = df_stats["diff mensal Abs."].rolling(6).mean()
    df_stats["Media Diff em 12M"] = df_stats["diff mensal Abs."].rolling(12).mean()
    df_stats["Media Diff em 24M"] = df_stats["diff mensal Abs."].rolling(24).mean()
    df_stats["Diff mensal Rel"] = df_stats["Valor"] / df_stats["leg"] - 1
    df_stats["Evolução Total em 6M"] = df_stats["Valor"].rolling(6).apply(lambda x: x[-1] - x[0])
    df_stats["Evolução Total em 12M"] = df_stats["Valor"].rolling(12).apply(lambda x: x[-1] - x[0])
    df_stats["Evolução Total em 24M"] = df_stats["Valor"].rolling(24).apply(lambda x: x[-1] - x[0])
    df_stats["Evolução Rel em 6M"] = df_stats["Valor"].rolling(6).apply(lambda x: x[-1] / x[0]-1 )
    df_stats["Evolução Rel em 12M"] = df_stats["Valor"].rolling(12).apply(lambda x: x[-1] / x[0]-1 )
    df_stats["Evolução Rel em 24M"] = df_stats["Valor"].rolling(24).apply(lambda x: x[-1] / x[0]-1 )

    df_stats = df_stats.drop("leg",axis=1)

    return df_stats

def metas_main():

            col1,col2 = st.columns(2)
            data_ref = col1.date_input("Patrimonio no Inicio da meta",max_value=df_stats.index.max())
            # %
            data_filter = df_stats.index[df_stats.index <= data_ref][-1]

            valor_inicio = df_stats.loc[data_filter]["Valor"]

            sal_bruto = col1.number_input("Salário Bruto",min_value=0.)
            sal_liq = col2.number_input("Salário Liquido",min_value=0.)

            custo_mensal = col2.number_input("Gasto mensal",min_value=0.)

            col1.markdown(f"**Valor no Inicio da meta**: R$ {valor_inicio:.2f}")

            selic_gov = get_selic()
            filter_selic = (selic_gov['DataInicioVigencia'] < data_ref) & (selic_gov['DataFimVigencia'] > data_ref)
            selic_default = selic_gov[filter_selic]['MetaSelic'].iloc[0]
            selic = st.number_input(label="Selic:",min_value=0.,value=selic_default,format="%.2f")
            selic = selic/100

            selic_mensal = ((1+selic)**(1/12) - 1)
            rendimento_anual = valor_inicio * selic
            rendimento_mensal = valor_inicio * ((1+selic)**(1/12) - 1)

            col1_selic,col2_selic = st.columns(2)

            with col1_selic:
                st.text(f"Selic mensal: {100*selic_mensal:.2f}")
                st.text(f"Selic anual: {100*selic:.2f}")

            with col2_selic:
                st.text(f"Rendimento mensal: R$ {rendimento_mensal:.2f}")
                st.text(f"Rendimento anual: R$ {rendimento_anual:.2f}")


            mensal= sal_bruto - custo_mensal + rendimento_mensal
            anual = mensal * 12

            col_pot1,col_pot2 = st.columns(2)
            with col_pot1.container(border=True):
                st.markdown(f"Potencial de arrecadação mensal : R$ {mensal:.2f}")
            with col_pot2.container(border=True):
                st.markdown(f"Potencial de arrecadação anual : R$ {anual:.2f}")

            with st.container(border=True):
                col_meta1,col_meta2 = st.columns(2)
                with col_meta1:
                    meta_estipulada = st.number_input(f"Meta Estipulada",min_value=0.,format="%.2f",value=anual)
                with col_meta2:
                    patrimonio_estipulado = anual + valor_inicio
                    st.markdown(f"Patrimonio Estipulado: \n\n R$ {patrimonio_estipulado:.2f}")

            return data_ref,valor_inicio,meta_estipulada,patrimonio_estipulado

st.set_page_config(page_title="Finanças",page_icon="💰")
st.markdown("""
# Boas Vindas!
## Nosso APP Financeiro!
Espero que voce curta a experiencia da nossa solucao para organizacao financeira.   
               
""")

# Variavel para ler arquivo
file_upload = st.file_uploader(label="Faça o upload aqui: ",type=["csv"])

# Verificando se exite dados 
if file_upload:

    # Carregando dados 
    df = pd.read_csv(file_upload)
    df["Data"] = pd.to_datetime(df["Data"],format="%d/%m/%Y").dt.date

    # Aba Dados bruto
    exp1 = st.expander("Dados brutos")

    columns_fmt = {"Valor":st.column_config.NumberColumn("Valor",format="R$ %f")} 
    exp1.dataframe(df,hide_index=True,column_config=columns_fmt)

    # Aba Instituições
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

    # Estatisticas Gerais
    exp3 = st.expander("Estatisticas gerais")
    df_stats = stats_geral(df)
    tab_stats,tab_abs,tab_rel = exp3.tabs(["Dados gerais","Historico de Evolução","Crescimento Relativo"])


    columns_config = {
        'Valor': st.column_config.NumberColumn("Valor",format="R$ %.0f"),
        'diff mensal Abs.' : st.column_config.NumberColumn('diff mensal Abs.' ,format="R$ %.2f"),
        "Media Diff em 6M" : st.column_config.NumberColumn("Media Diff em 6M" ,format="R$ %.2f"),
        "Media Diff em 12M" : st.column_config.NumberColumn("Media Diff em 12M" ,format="R$ %.2f"),
        "Media Diff em 24M" : st.column_config.NumberColumn("Media Diff em 24M" ,format="R$ %.2f"),
        "Evolução Total em 6M" : st.column_config.NumberColumn("Evolução Total em 6M" ,format="R$ %.2f"),
        "Evolução Total em 12M" : st.column_config.NumberColumn("Evolução Total em 12M" ,format="R$ %.2f"),
        "Evolução Total em 24M" : st.column_config.NumberColumn("Evolução Total em 24M" ,format="R$ %.2f"),
        "Evolução Rel em 24M" : st.column_config.NumberColumn("Evolução Rel em 24M" ,format="percent"),
        "Evolução Rel em 12M" : st.column_config.NumberColumn("Evolução Rel em 12M" ,format="percent"),
        "Evolução Rel em 6M" : st.column_config.NumberColumn("Evolução Rel em 6M" ,format="percent"),
        "Diff mensal Rel" : st.column_config.NumberColumn("Diff mensal Rel" ,format="percent"),

    }

    with tab_stats:
        st.dataframe(df_stats, column_config=columns_config)

    with tab_abs:

        columns_abs = [
                'diff mensal Abs.' ,
                "Media Diff em 6M" ,
                "Media Diff em 12M" ,
                "Media Diff em 24M" ,
            
        ]
        st.line_chart(df_stats[columns_abs])

    with tab_rel:

        columns_rel = [
            "Evolução Rel em 24M" ,
            "Evolução Rel em 12M" ,
            "Evolução Rel em 6M" ,
            "Diff mensal Rel" ,
        ]
        st.line_chart(df_stats[columns_rel])

    # Aba Metas 

    with st.expander("Metas"):

        tab_main,tab_dados,tab_graph = st.tabs(['Configuração','Dados','Grafico'])

        with tab_main:

            data_ref,valor_inicio,meta_estipulada,patrimonio_estipulado= metas_main()

        with tab_dados:
            
            df_patrimonio = df_stats.reset_index()[['Data','Valor']]
            df_patrimonio['Data Referencia'] = pd.to_datetime(df_patrimonio["Data"]).dt.strftime("%Y-%m")
            meses = pd.DataFrame({"Data Referencia":[(data_ref + pd.DateOffset(months=i)) for i in range(1,13)]
                                  ,"Meta Mensal":[(valor_inicio+round(meta_estipulada/12,2) * i) for i in range(1,13)] })
            meses['Data Referencia'] = pd.to_datetime(meses['Data Referencia']).dt.strftime("%Y-%m")
            meses = meses.merge(df_patrimonio,how='left',on='Data Referencia')
            meses = meses[["Data Referencia","Meta Mensal","Valor"]]
            meses['Atingimento (%)'] = meses['Valor'] / meses['Meta Mensal']
            meses['Atingimento ano'] = meses['Valor'] / patrimonio_estipulado
            meses['Atingimento Esperado'] = meses['Meta Mensal'] / patrimonio_estipulado
            meses = meses.set_index(['Data Referencia'])

            columns_config_meses = {"Meta Mensal":st.column_config.NumberColumn("Meta Mensal",format="R$ %.2f")
                                    ,"Valor":st.column_config.NumberColumn("Valor Atingido",format="R$ %.2f")
                                    ,"Atingimento (%)":st.column_config.NumberColumn("Atingimento (%)",format="percent")
                                    ,"Atingimento ano":st.column_config.NumberColumn("Atingimento ano",format="percent")
                                    ,"Atingimento Esperado":st.column_config.NumberColumn("Atingimento Esperado",format="percent")}

            st.dataframe(meses,column_config=columns_config_meses)

        with tab_graph:
            st.line_chart(meses[['Atingimento ano','Atingimento Esperado']])
            

# Nao há dados no arquivo