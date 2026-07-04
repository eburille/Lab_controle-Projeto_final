import os
import glob
import pandas as pd
import matplotlib.pyplot as plt

def obter_csv_mais_recente():
    """ Encontra o arquivo de histórico mais recente na pasta atual """
    arquivos = glob.glob("historico_posicao_*.csv")
    if not arquivos:
        return None
    # Ordena os arquivos pela data de modificação e retorna o mais novo
    return max(arquivos, key=os.path.getmtime)

def plotar_historico(nome_arquivo=None):
    # Se nenhum arquivo for especificado, busca o último gerado
    if nome_arquivo is None:
        nome_arquivo = obter_csv_mais_recente()
        if nome_arquivo is None:
            print("Erro: Nenhum arquivo 'historico_posicao_*.csv' encontrado na pasta!")
            return
    
    print(f"Lendo e renderizando dados de: {nome_arquivo}")
    
    # Carrega os dados usando o Pandas
    try:
        dados = pd.read_csv(nome_arquivo)
    except Exception as e:
        print(f"Erro ao ler o arquivo CSV: {e}")
        return

    # Extrai as colunas baseadas no cabeçalho estipulado na interface
    tempo = dados["Tempo (s)"]
    posicao = dados["Posicao (rad)"]
    controle = dados["controle"]

    # --- CONFIGURAÇÃO DO GRÁFICO (Estilo Engenharia) ---
    plt.figure(figsize=(10, 5))
    
    # Plota a curva de resposta temporal da posição
    plt.plot(tempo, posicao, label="Posição medida", color="b", linewidth=2)
    plt.plot(tempo, controle, label="Sinal de controle", color="r", linewidth=2)

    
    # Estilização do Gráfico (Dark/Modern Mode condizente com a GUI)
    plt.title(f"Resposta Temporal do Sistema\nArquivo: {nome_arquivo}", fontsize=12, fontweight='bold', color='#121212')
    plt.xlabel("Tempo (segundos)", fontsize=10, fontweight='bold')
    plt.ylabel("Posição (radianos)", fontsize=10, fontweight='bold')
    
    # Ativa a grade (grid) para facilitar a análise de overshoot e regime permanente
    plt.grid(True, linestyle="--", alpha=0.6, color="#CCCCCC")
    plt.legend(loc="upper right")
    
    # Otimiza as margens do gráfico
    plt.tight_layout()
    
    # Exibe a janela gráfica na tela local do Linux
    plt.show()

if __name__ == '__main__':
    # Roda o plotter para o último teste executado
    plotar_historico()
    
    # Caso queira plotar um arquivo específico do passado, basta descomentar a linha abaixo:
    # plotar_historico("historico_posicao_1719600000.csv")