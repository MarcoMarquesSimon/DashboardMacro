# -*- coding: utf-8 -*-
"""
Created on Thu Feb 26 10:00:24 2026

@author: usuar

Programa que carrega funções para puxar dados para fazer o dashboard.
"""

# Importação de bibliotecas
import pandas as pd

"""
Função para puxar dados do tesouro
"""

def dados_tesouro(url) :
    
    # Lendo arquivo do tesouro 
    df = pd.read_csv(url, sep=';')
    
    # Tranformando as colunas 'Data Vencimento' e 'Data Base' em data
    df['Data Vencimento'] = pd.to_datetime(df['Data Vencimento'], format='%d/%m/%Y')
    df['Data Base'] = pd.to_datetime(df['Data Base'], format='%d/%m/%Y')
    
    # Tranformando on restante das colunas em numéricas
    for coluna in df.columns[3:] :
        df[coluna] = df[coluna].replace(",", ".", regex=True)
        df[coluna] = df[coluna].astype("float")
        
    return df