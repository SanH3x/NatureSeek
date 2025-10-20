from flask import Flask, render_template, request, redirect, url_for, flash
import pandas as pd
import os
from datetime import datetime
from collections import Counter
import numpy as np

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'chave-desenvolvimento')

# Configurações
ARQUIVO_CSV = 'dados_agricolas.csv'

def inicializar_csv():
    """Inicializa o arquivo CSV com cabeçalhos se não existir"""
    if not os.path.exists(ARQUIVO_CSV):
        df = pd.DataFrame(columns=[
            'id', 'cultivo', 'praga', 'hectares', 'defensivo', 
            'cidade', 'data_cadastro'
        ])
        df.to_csv(ARQUIVO_CSV, index=False, encoding='utf-8')

def gerar_id():
    """Gera um ID único para cada registro"""
    try:
        df = ler_dados()
        if len(df) == 0:
            return 1
        return df['id'].max() + 1
    except:
        return 1

def salvar_dados(dados):
    """Salva os dados no CSV"""
    df = ler_dados()
    novo_registro = pd.DataFrame([dados])
    df = pd.concat([df, novo_registro], ignore_index=True)
    df.to_csv(ARQUIVO_CSV, index=False, encoding='utf-8')

def ler_dados():
    """Lê todos os dados do CSV com tratamento de erros"""
    try:
        # Tenta ler com encoding utf-8 primeiro
        df = pd.read_csv(ARQUIVO_CSV, encoding='utf-8')
    except UnicodeDecodeError:
        try:
            # Se falhar, tenta latin-1
            df = pd.read_csv(ARQUIVO_CSV, encoding='latin-1')
        except:
            # Se ainda falhar, cria DataFrame vazio
            df = pd.DataFrame(columns=[
                'id', 'cultivo', 'praga', 'hectares', 'defensivo', 
                'cidade', 'data_cadastro'
            ])
    except FileNotFoundError:
        # Se o arquivo não existir, cria DataFrame vazio
        df = pd.DataFrame(columns=[
            'id', 'cultivo', 'praga', 'hectares', 'defensivo', 
            'cidade', 'data_cadastro'
        ])
    except Exception as e:
        print(f"Erro ao ler CSV: {e}")
        df = pd.DataFrame(columns=[
            'id', 'cultivo', 'praga', 'hectares', 'defensivo', 
            'cidade', 'data_cadastro'
        ])
    
    # Garantir que os tipos de dados estão corretos
    if not df.empty:
        df['id'] = pd.to_numeric(df['id'], errors='coerce').fillna(0).astype(int)
        df['hectares'] = pd.to_numeric(df['hectares'], errors='coerce').fillna(0.0)
        
        # Limpar strings - remover espaços extras e garantir encoding
        string_columns = ['cultivo', 'praga', 'defensivo', 'cidade']
        for col in string_columns:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip().str.title()
    
    return df

def processar_lista_string(texto):
    """Processa strings que podem conter múltiplos valores separados por vírgula"""
    if pd.isna(texto) or texto == 'nan':
        return []
    
    texto = str(texto).strip()
    if not texto:
        return []
    
    # Divide por vírgula e remove espaços extras
    itens = [item.strip() for item in texto.split(',')]
    # Filtra itens vazios e aplica title case
    return [item.title() for item in itens if item]

def calcular_frequencias_pragas_defensivos(df):
    """Calcula a frequência de pragas e defensivos, tratando valores múltiplos"""
    frequencias = {
        'pragas_por_cultivo': {},
        'defensivos_por_cultivo': {},
        'pragas_por_defensivo': {},
        'defensivos_por_praga': {},
        'pragas_individual': {},
        'defensivos_individual': {}
    }
    
    if df.empty:
        return frequencias
    
    # Listas para armazenar todos os itens individuais
    todas_pragas = []
    todos_defensivos = []
    
    # Processar cada linha para extrair pragas e defensivos individuais
    for _, row in df.iterrows():
        cultivo = str(row['cultivo']).strip().title() if pd.notna(row['cultivo']) else 'Desconhecido'
        
        # Processar pragas (pode ser string única ou múltiplas separadas por vírgula)
        pragas = processar_lista_string(row['praga'])
        todas_pragas.extend(pragas)
        
        # Processar defensivos (pode ser string única ou múltiplas separadas por vírgula)
        defensivos = processar_lista_string(row['defensivo'])
        todos_defensivos.extend(defensivos)
        
        # Adicionar ao dicionário de pragas por cultivo
        if cultivo not in frequencias['pragas_por_cultivo']:
            frequencias['pragas_por_cultivo'][cultivo] = {}
        
        for praga in pragas:
            if praga in frequencias['pragas_por_cultivo'][cultivo]:
                frequencias['pragas_por_cultivo'][cultivo][praga] += 1
            else:
                frequencias['pragas_por_cultivo'][cultivo][praga] = 1
        
        # Adicionar ao dicionário de defensivos por cultivo
        if cultivo not in frequencias['defensivos_por_cultivo']:
            frequencias['defensivos_por_cultivo'][cultivo] = {}
        
        for defensivo in defensivos:
            if defensivo in frequencias['defensivos_por_cultivo'][cultivo]:
                frequencias['defensivos_por_cultivo'][cultivo][defensivo] += 1
            else:
                frequencias['defensivos_por_cultivo'][cultivo][defensivo] = 1
    
    # Calcular frequências individuais
    frequencias['pragas_individual'] = dict(Counter(todas_pragas))
    frequencias['defensivos_individual'] = dict(Counter(todos_defensivos))
    
    # Calcular pragas por defensivo e defensivos por praga
    for _, row in df.iterrows():
        pragas = processar_lista_string(row['praga'])
        defensivos = processar_lista_string(row['defensivo'])
        
        for defensivo in defensivos:
            if defensivo not in frequencias['pragas_por_defensivo']:
                frequencias['pragas_por_defensivo'][defensivo] = {}
            
            for praga in pragas:
                if praga in frequencias['pragas_por_defensivo'][defensivo]:
                    frequencias['pragas_por_defensivo'][defensivo][praga] += 1
                else:
                    frequencias['pragas_por_defensivo'][defensivo][praga] = 1
        
        for praga in pragas:
            if praga not in frequencias['defensivos_por_praga']:
                frequencias['defensivos_por_praga'][praga] = {}
            
            for defensivo in defensivos:
                if defensivo in frequencias['defensivos_por_praga'][praga]:
                    frequencias['defensivos_por_praga'][praga][defensivo] += 1
                else:
                    frequencias['defensivos_por_praga'][praga][defensivo] = 1
    
    return frequencias

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        try:
            # Processar campos que podem ter múltiplos valores
            cultivo = request.form['cultivo'].strip().title()
            praga = request.form['praga'].strip().title()  # Pode conter vírgulas
            defensivo = request.form['defensivo'].strip().title()  # Pode conter vírgulas
            cidade = request.form['cidade'].strip().title()
            
            dados = {
                'id': gerar_id(),
                'cultivo': cultivo,
                'praga': praga,
                'hectares': float(request.form['hectares']),
                'defensivo': defensivo,
                'cidade': cidade,
                'data_cadastro': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            if dados['hectares'] <= 0:
                flash('A área em hectares deve ser maior que zero!', 'error')
                return render_template('cadastro.html')
            
            salvar_dados(dados)
            flash('Cadastro realizado com sucesso!', 'success')
            return redirect(url_for('cadastro'))
            
        except ValueError:
            flash('Por favor, insira valores válidos para hectares!', 'error')
        except Exception as e:
            flash(f'Erro ao cadastrar: {str(e)}', 'error')
    
    return render_template('cadastro.html')

@app.route('/consulta')
def consulta():
    df = ler_dados()
    
    filtro_cultivo = request.args.get('filtro_cultivo', '')
    filtro_cidade = request.args.get('filtro_cidade', '')
    
    if filtro_cultivo:
        df = df[df['cultivo'].str.contains(filtro_cultivo, case=False, na=False)]
    if filtro_cidade:
        df = df[df['cidade'].str.contains(filtro_cidade, case=False, na=False)]
    
    dados = df.to_dict('records')
    
    return render_template('consulta.html', dados=dados, 
                         filtro_cultivo=filtro_cultivo, 
                         filtro_cidade=filtro_cidade)

@app.route('/estatisticas')
def estatisticas():
    df = ler_dados()
    
    if len(df) == 0:
        return render_template('estatisticas.html', 
                             estatisticas=None, 
                             totais=None,
                             frequencias=None,
                             mensagem="Nenhum dado cadastrado para análise.")
    
    try:
        # Estatísticas gerais
        estatisticas_gerais = {
            'total_registros': len(df),
            'total_hectares': df['hectares'].sum(),
            'media_hectares': df['hectares'].mean(),
            'maior_area': df['hectares'].max(),
            'menor_area': df['hectares'].min(),
            'total_cultivos': df['cultivo'].nunique(),
            'total_cidades': df['cidade'].nunique()
        }
        
        # Calcular totais de pragas e defensivos únicos (considerando valores múltiplos)
        todas_pragas = []
        todos_defensivos = []
        
        for _, row in df.iterrows():
            pragas = processar_lista_string(row['praga'])
            defensivos = processar_lista_string(row['defensivo'])
            todas_pragas.extend(pragas)
            todos_defensivos.extend(defensivos)
        
        estatisticas_gerais['total_pragas'] = len(set(todas_pragas))
        estatisticas_gerais['total_defensivos'] = len(set(todos_defensivos))
        
        # Contagens por categoria (para valores únicos)
        totais = {
            'cultivos': df['cultivo'].value_counts().to_dict(),
            'cidades': df['cidade'].value_counts().to_dict(),
            'pragas_unicas': dict(Counter(todas_pragas)),
            'defensivos_unicos': dict(Counter(todos_defensivos))
        }
        
        # Frequências detalhadas
        frequencias = calcular_frequencias_pragas_defensivos(df)
        
        # Debug: imprimir algumas informações
        print(f"Total de registros: {len(df)}")
        print(f"Pragas encontradas: {set(todas_pragas)}")
        print(f"Defensivos encontrados: {set(todos_defensivos)}")
        
        return render_template('estatisticas.html', 
                             estatisticas=estatisticas_gerais,
                             totais=totais,
                             frequencias=frequencias)
    
    except Exception as e:
        print(f"Erro ao calcular estatísticas: {e}")
        flash(f'Erro ao calcular estatísticas: {str(e)}', 'error')
        return render_template('estatisticas.html', 
                             estatisticas=None, 
                             totais=None,
                             frequencias=None)

@app.route('/excluir/<int:id>')
def excluir(id):
    try:
        df = ler_dados()
        df = df[df['id'] != id]
        df.to_csv(ARQUIVO_CSV, index=False, encoding='utf-8')
        flash('Registro excluído com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao excluir registro: {str(e)}', 'error')
    
    return redirect(url_for('consulta'))

if __name__ == '__main__':
    # Criar pastas necessárias
    if not os.path.exists('templates'):
        os.makedirs('templates')
    if not os.path.exists('static'):
        os.makedirs('static')
    
    inicializar_csv()
    
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    app.run(host='0.0.0.0', port=port, debug=debug)