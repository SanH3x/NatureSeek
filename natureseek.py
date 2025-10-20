from flask import Flask, render_template, request, redirect, url_for, flash
import pandas as pd
import os
from datetime import datetime
from collections import Counter

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
        df.to_csv(ARQUIVO_CSV, index=False)

def gerar_id():
    """Gera um ID único para cada registro"""
    try:
        df = pd.read_csv(ARQUIVO_CSV)
        if len(df) == 0:
            return 1
        return df['id'].max() + 1
    except:
        return 1

def salvar_dados(dados):
    """Salva os dados no CSV"""
    df = pd.read_csv(ARQUIVO_CSV)
    novo_registro = pd.DataFrame([dados])
    df = pd.concat([df, novo_registro], ignore_index=True)
    df.to_csv(ARQUIVO_CSV, index=False)

def ler_dados():
    """Lê todos os dados do CSV"""
    try:
        return pd.read_csv(ARQUIVO_CSV)
    except:
        return pd.DataFrame()

def calcular_frequencias_pragas_defensivos(df):
    """Calcula a frequência de pragas e defensivos por cultivo"""
    frequencias = {
        'pragas_por_cultivo': {},
        'defensivos_por_cultivo': {},
        'pragas_por_defensivo': {},
        'defensivos_por_praga': {}
    }
    
    # Frequência de pragas por cultivo
    for cultivo in df['cultivo'].unique():
        pragas_cultivo = df[df['cultivo'] == cultivo]['praga'].tolist()
        frequencias['pragas_por_cultivo'][cultivo] = dict(Counter(pragas_cultivo))
    
    # Frequência de defensivos por cultivo
    for cultivo in df['cultivo'].unique():
        defensivos_cultivo = df[df['cultivo'] == cultivo]['defensivo'].tolist()
        frequencias['defensivos_por_cultivo'][cultivo] = dict(Counter(defensivos_cultivo))
    
    # Frequência de pragas por defensivo
    for defensivo in df['defensivo'].unique():
        pragas_defensivo = df[df['defensivo'] == defensivo]['praga'].tolist()
        frequencias['pragas_por_defensivo'][defensivo] = dict(Counter(pragas_defensivo))
    
    # Frequência de defensivos por praga
    for praga in df['praga'].unique():
        defensivos_praga = df[df['praga'] == praga]['defensivo'].tolist()
        frequencias['defensivos_por_praga'][praga] = dict(Counter(defensivos_praga))
    
    return frequencias

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        try:
            dados = {
                'id': gerar_id(),
                'cultivo': request.form['cultivo'].strip().title(),
                'praga': request.form['praga'].strip().title(),
                'hectares': float(request.form['hectares']),
                'defensivo': request.form['defensivo'].strip().title(),
                'cidade': request.form['cidade'].strip().title(),
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
    filtro_praga = request.args.get('filtro_praga', '')
    
    if filtro_cultivo:
        df = df[df['cultivo'].str.contains(filtro_cultivo, case=False, na=False)]
    if filtro_praga:
        df = df[df['praga'].str.contains(filtro_praga, case=False, na=False)]
    
    dados = df.to_dict('records')
    
    return render_template('consulta.html', dados=dados, 
                         filtro_cultivo=filtro_cultivo, 
                         filtro_praga=filtro_praga)


@app.route('/estatisticas')
def estatisticas():
    df = ler_dados()
    
    if len(df) == 0:
        return render_template('estatisticas.html', 
                             estatisticas=None, 
                             totais=None, frequencias=None, mensagem="Nenhum dado cadastrado para análise.")
    
    try:
        # Estatísticas gerais
        estatisticas_gerais = {
            'total_registros': len(df),
            'total_hectares': df['hectares'].sum(),
            'media_hectares': df['hectares'].mean(),
            'maior_area': df['hectares'].max(),
            'menor_area': df['hectares'].min(),
            'total_cultivos': df['cultivo'].nunique(),
            'total_pragas': df['praga'].nunique(),
            'total_defensivos': df['defensivo'].nunique(),
            'total_cidades': df['cidade'].nunique()
        }
        
        # Contagens por categoria
        totais = {
            'cultivos': df['cultivo'].value_counts().to_dict(),
            'pragas': df['praga'].value_counts().to_dict(),
            'defensivos': df['defensivo'].value_counts().to_dict(),
            'cidades': df['cidade'].value_counts().to_dict()
        }
        
        # Frequências detalhadas
        frequencias = calcular_frequencias_pragas_defensivos(df)
        
        return render_template('estatisticas.html', 
                             estatisticas=estatisticas_gerais, totais=totais, frequencias=frequencias)
    
    except Exception as e:
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
        df.to_csv(ARQUIVO_CSV, index=False)
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
