import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Dashboard Chassi", layout="wide")

st.title("🏎️ Matriz de Decisão: Protótipo do Chassi")
st.markdown("Selecione os materiais no menu lateral esquerdo para comparar os critérios de desempenho em tempo real.")

# --- 2. LEITURA DE DADOS (CACHE) ---
# O cache faz com que o Streamlit não tenha de ler o Excel sempre que clicas num botão
@st.cache_data
def carregar_dados():
    # Modo Nuvem: Lê apenas o nome do ficheiro que está junto dele no GitHub
    try:
        # Tenta primeiro a versão SEM til (como estava na sua pasta original)
        return pd.read_excel('Matriz de Decisao Chassi- Prototipo_VFINAL.xlsx', sheet_name='Decision Matrix', skiprows=14, nrows=7)
    except:
        try:
            # Tenta a versão COM til (caso o nome no GitHub esteja assim)
            return pd.read_excel('Matriz de Decisão Chassi- Prototipo_VFINAL.xlsx', sheet_name='Decision Matrix', skiprows=14, nrows=7)
        except Exception as e:
            st.error("Erro: O ficheiro Excel não foi encontrado junto ao script no GitHub. Confirme se o nome está idêntico.")
            return None

df = carregar_dados()

if df is not None:
    # --- 3.MAPEAMENTO INTELIGENTE DE COLUNAS ---
    # Sabendo que as notas começam na coluna 4 e saltam de 2 em 2 (Nota e Nota Ponderada)
    nomes_materiais = [
        'Fibra de Carbono', 'Fibra de Vidro', 'Aramida', 'Alumínio CHASSI', 
        'Aço 1020', 'Aço 4340', 'Aço 4130', 'Aço 1010', 'Titânio', 'Alumínio (Padrão)', 'Aço Inox'
    ]
    
    materiais_map = {}
    idx = 4
    for nome in nomes_materiais:
        if idx < len(df.columns):
            materiais_map[nome] = idx
        idx += 2

    # --- 4. BARRA LATERAL (CHECKBOXES) ---
    st.sidebar.header("⚙️ Materiais para Análise")
    st.sidebar.write("Marca ou desmarca para atualizar os gráficos:")
    
    selecionados = []
    # Materiais que já começam selecionados por padrão
    padroes = ['Fibra de Carbono', 'Alumínio CHASSI', 'Aço 1020']
    
    for mat in materiais_map.keys():
        # Cria a checkbox. Se o utilizador a marcar, entra na lista 'selecionados'
        if st.sidebar.checkbox(mat, value=(mat in padroes)):
            selecionados.append(mat)

    # --- 5. EXIBIÇÃO DE GRÁFICOS E TABELAS ---
    if not selecionados:
        st.warning("👈 Por favor, seleciona pelo menos um material na barra lateral.")
    else:
        # Separa os Critérios (Linhas 0 a 5) do Total Final (Linha 6)
        df_criterios = df.iloc[:6] 
        df_totais = df.iloc[6]     
        criterios = df_criterios.iloc[:, 0].tolist()

        # Divide o ecrã em duas colunas para os gráficos ficarem lado a lado
        col1, col2 = st.columns(2)

        # GRÁFICO 1: RADAR DE DESEMPENHO
        with col1:
            st.subheader("🎯 Comparativo por Critério (Radar)")
            fig_radar = go.Figure()
            
            for mat in selecionados:
                col_idx = materiais_map[mat]
                notas = df_criterios.iloc[:, col_idx].fillna(0).tolist()
                
                # Fechar o polígono do radar repetindo a primeira nota no fim
                notas += [notas[0]]
                criterios_fechados = criterios + [criterios[0]]
                
                fig_radar.add_trace(go.Scatterpolar(
                    r=notas,
                    theta=criterios_fechados,
                    fill='toself',
                    name=mat,
                    opacity=0.7
                ))
            
            fig_radar.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 5.5])),
                showlegend=True,
                margin=dict(l=40, r=40, t=40, b=40)
            )
            st.plotly_chart(fig_radar, use_container_width=True)

        # GRÁFICO 2: PONTUAÇÃO TOTAL PONDERADA
        with col2:
            st.subheader("🏆 Pontuação Final Ponderada")
            dados_barras = []
            
            for mat in selecionados:
                col_idx = materiais_map[mat]
                # A pontuação final está sempre na coluna à direita (+1) da nota
                pontuacao = df_totais.iloc[col_idx + 1]
                dados_barras.append({'Material': mat, 'Pontuação': pontuacao})
            
            df_barras = pd.DataFrame(dados_barras).sort_values(by='Pontuação', ascending=False)
            
            fig_bar = px.bar(
                df_barras, 
                x='Material', 
                y='Pontuação', 
                text='Pontuação',
                color='Material',
                color_discrete_sequence=px.colors.qualitative.Plotly
            )
            fig_bar.update_traces(texttemplate='%{text:.1f}', textposition='outside')
            fig_bar.update_layout(yaxis_range=[0, max(df_barras['Pontuação']) * 1.2], showlegend=False)
            st.plotly_chart(fig_bar, use_container_width=True)

        # TABELA: A MATRIZ DINÂMICA
        st.markdown("---")
        st.subheader("📋 Matriz de Decisão Dinâmica")
        
        # Constrói a tabela apenas com as colunas escolhidas
        colunas_para_mostrar = [df.columns[0], df.columns[1]] 
        nomes_tabela = ['Critério', 'Peso']
        
        for mat in selecionados:
            col_idx = materiais_map[mat]
            colunas_para_mostrar.append(df.columns[col_idx])
            colunas_para_mostrar.append(df.columns[col_idx + 1])
            nomes_tabela.append(f"{mat} (Nota)")
            nomes_tabela.append(f"{mat} (Ponderado)")
        
        df_limpo = df[colunas_para_mostrar].copy()
        df_limpo.columns = nomes_tabela
        
        # 💡 O GRANDE TRUQUE: Transformar 'Critério' e 'Peso' no Índice da tabela.
        # Isso faz o Streamlit fixá-las automaticamente ao fazer scroll para a direita!
        df_fixo = df_limpo.set_index(['Critério', 'Peso'])
        
        # Mostra a tabela interativa com as colunas congeladas
        st.dataframe(df_fixo, use_container_width=True)