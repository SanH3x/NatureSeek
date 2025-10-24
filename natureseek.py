from flask import Flask, render_template, request, redirect, url_for, flash
import csv
import os
from datetime import datetime
from pathlib import Path

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui'

# Configuração
CSV_FILE = 'dados_agricolas.csv'
CSV_HEADERS = ['cultivo', 'praga', 'hectares', 'defensivo', 'cidade_plantio', 'data_cadastro']

def init_csv():
    """Inicializa o arquivo CSV se não existir"""
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, 'w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=CSV_HEADERS)
            writer.writeheader()


def read_csv():
    """Lê todos os dados do CSV"""
    try:
        with open(CSV_FILE, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            return list(reader)
    except:
        return []

def write_csv(data):
    """Escreve dados no CSV"""
    with open(CSV_FILE, 'w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=CSV_HEADERS)
        writer.writeheader()
        writer.writerows(data)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        cultivo = request.form['cultivo'].strip()
        praga = request.form['praga'].strip()
        hectares = request.form['hectares'].strip()
        defensivo = request.form['defensivo'].strip()
        cidade = request.form['cidade'].strip()
        
        try:
            # Validar dados
            if not all([cultivo, praga, hectares, defensivo, cidade]):
                flash('Todos os campos são obrigatórios!', 'error')
                return render_template('cadastro.html')
            
            hectares_float = float(hectares)
            if hectares_float <= 0:
                flash('Hectares deve ser maior que zero!', 'error')
                return render_template('cadastro.html')
            
            # Ler dados existentes
            dados_existentes = read_csv()
            
            # Novo registro
            novo_registro = {
                'cultivo': cultivo,
                'praga': praga,
                'hectares': hectares_float,
                'defensivo': defensivo,
                'cidade_plantio': cidade,
                'data_cadastro': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Adicionar e salvar
            dados_existentes.append(novo_registro)
            write_csv(dados_existentes)
            
            flash('Registro cadastrado com sucesso!', 'success')
            return redirect(url_for('cadastro'))
            
        except ValueError:
            flash('Hectares deve ser um número válido!', 'error')
        except Exception as e:
            flash(f'Erro ao cadastrar: {str(e)}', 'error')
    
    return render_template('cadastro.html')

@app.route('/consulta')
def consulta():
    try:
        filtro_cultivo = request.args.get('cultivo', '').strip()
        filtro_praga = request.args.get('praga', '').strip()
        filtro_cidade = request.args.get('cidade', '').strip()
        
        # Ler todos os dados
        dados = read_csv()
        
        # Aplicar filtros
        dados_filtrados = []
        for registro in dados:
            cultivo_match = not filtro_cultivo or filtro_cultivo.lower() in registro['cultivo'].lower()
            praga_match = not filtro_praga or filtro_praga.lower() in registro['praga'].lower()
            cidade_match = not filtro_cidade or filtro_cidade.lower() in registro['cidade_plantio'].lower()
            
            if cultivo_match and praga_match and cidade_match:
                dados_filtrados.append(registro)
        
        return render_template('consulta.html', 
                             dados=dados_filtrados,
                             filtro_cultivo=filtro_cultivo,
                             filtro_praga=filtro_praga,
                             filtro_cidade=filtro_cidade)
                             
    except Exception as e:
        flash(f'Erro na consulta: {str(e)}', 'error')
        return render_template('consulta.html', dados=[], 
                             filtro_cultivo='', filtro_praga='', filtro_cidade='')

@app.route('/excluir/<int:id>')
def excluir(id):
    try:
        # Ler dados existentes
        dados = read_csv()
        
        # Filtrar excluindo o ID
        dados_atualizados = [row for row in dados if int(row['id']) != id]
        
        # Verificar se algum registro foi removido
        if len(dados_atualizados) == len(dados):
            flash('Registro não encontrado!', 'error')
        else:
            write_csv(dados_atualizados)
            flash('Registro excluído com sucesso!', 'success')
            
    except Exception as e:
        flash(f'Erro ao excluir: {str(e)}', 'error')
    
    return redirect(url_for('consulta'))

@app.route('/estatisticas')
def estatisticas():
    try:
        dados = read_csv()
        
        if not dados:
            return render_template('estatisticas.html', totais={})
        
        # Calcular estatísticas
        total_registros = len(dados)
        total_hectares = sum(float(row['hectares']) for row in dados)
        
        # Distribuição por cultivo
        cultivos = {}
        for row in dados:
            cultivo = row['cultivo']
            cultivos[cultivo] = cultivos.get(cultivo, 0) + 1
        
        # Pragas únicas
        pragas_unicas = {}
        for row in dados:
            praga = row['praga']
            pragas_unicas[praga] = pragas_unicas.get(praga, 0) + 1
        
        # Defensivos únicos
        defensivos_unicos = {}
        for row in dados:
            defensivo = row['defensivo']
            defensivos_unicos[defensivo] = defensivos_unicos.get(defensivo, 0) + 1
        
        # Cidades
        cidades = {}
        for row in dados:
            cidade = row['cidade_plantio']
            cidades[cidade] = cidades.get(cidade, 0) + 1
        
        totais = {
            'total_registros': total_registros,
            'total_hectares': total_hectares,
            'cultivos': cultivos,
            'pragas_unicas': pragas_unicas,
            'defensivos_unicos': defensivos_unicos,
            'cidades': cidades
        }
        
        return render_template('estatisticas.html', totais=totais)
        
    except Exception as e:
        flash(f'Erro ao carregar estatísticas: {str(e)}', 'error')
        return render_template('estatisticas.html', totais={})

if __name__ == '__main__':
    init_csv()
    app.run(debug=True)
