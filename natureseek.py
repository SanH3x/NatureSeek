from flask import Flask, render_template, request, redirect, url_for, flash
import csv
import os
from datetime import datetime
from pathlib import Path
from collections import Counter

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui'

# Configuração
CSV_FILE = 'dados_agricolas.csv'
CSV_HEADERS = ['id', 'cultivo', 'praga', 'hectares', 'defensivo', 'cidade', 'data_cadastro']

def init_csv():
    """Inicializa o arquivo CSV se não existir"""
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, 'w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=CSV_HEADERS)
            writer.writeheader()

def get_next_id():
    """Obtém o próximo ID disponível"""
    try:
        with open(CSV_FILE, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            rows = list(reader)
            if not rows:
                return 1
            return max(int(row['id']) for row in rows) + 1
    except:
        return 1

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

def formatar_data(data_str):
    """Formata a data para exibição"""
    try:
        if ' ' in data_str:
            data_obj = datetime.strptime(data_str, '%Y-%m-%d %H:%M:%S')
            return data_obj.strftime('%d/%m/%Y')
        else:
            return data_str
    except:
        return data_str

def processar_termos_separados_por_virgula(texto):
    """
    Processa texto com termos separados por vírgula
    Retorna lista de termos limpos e normalizados
    """
    if not texto:
        return []
    
    # Divide por vírgula, remove espaços extras e filtra strings vazias
    termos = [termo.strip() for termo in texto.split(',')]
    termos = [termo for termo in termos if termo]  # Remove strings vazias
    
    return termos

def calcular_totais_frequencias(dados):
    """Calcula totais e frequências considerando termos separados por vírgula"""
    if not dados:
        return {}
    
    total_registros = len(dados)
    total_hectares = sum(float(row.get('hectares', 0)) for row in dados)
    
    # Inicializar contadores
    frequencia_cultivos = Counter()
    frequencia_pragas = Counter()
    frequencia_defensivos = Counter()
    frequencia_cidades = Counter()
    
    # Processar cada registro
    for row in dados:
        # Cultivos - geralmente um único valor, mas processamos como lista para consistência
        cultivos = processar_termos_separados_por_virgula(row.get('cultivo', ''))
        for cultivo in cultivos:
            frequencia_cultivos[cultivo] += 1
        
        # Pragas - podem ter múltiplos valores separados por vírgula
        pragas = processar_termos_separados_por_virgula(row.get('praga', ''))
        for praga in pragas:
            frequencia_pragas[praga] += 1
        
        # Defensivos - podem ter múltiplos valores separados por vírgula
        defensivos = processar_termos_separados_por_virgula(row.get('defensivo', ''))
        for defensivo in defensivos:
            frequencia_defensivos[defensivo] += 1
        
        # Cidades - geralmente um único valor
        cidades = processar_termos_separados_por_virgula(row.get('cidade', ''))
        for cidade in cidades:
            frequencia_cidades[cidade] += 1
    
    # Calcular percentuais de forma segura
    def calcular_percentuais(frequencias, total):
        if total == 0:
            return {}
        return {item: {
            'frequencia': freq,
            'percentual': round((freq / total) * 100, 2)
        } for item, freq in frequencias.items()}
    
    return {
        'total_registros': total_registros,
        'total_hectares': total_hectares,
        'frequencia_cultivos': calcular_percentuais(
            dict(sorted(frequencia_cultivos.items(), key=lambda x: x[1], reverse=True)), 
            total_registros
        ),
        'frequencia_pragas': calcular_percentuais(
            dict(sorted(frequencia_pragas.items(), key=lambda x: x[1], reverse=True)), 
            total_registros
        ),
        'frequencia_defensivos': calcular_percentuais(
            dict(sorted(frequencia_defensivos.items(), key=lambda x: x[1], reverse=True)), 
            total_registros
        ),
        'frequencia_cidades': calcular_percentuais(
            dict(sorted(frequencia_cidades.items(), key=lambda x: x[1], reverse=True)), 
            total_registros
        ),
        # Estatísticas adicionais sobre múltiplos termos
        'estatisticas_multiplos': {
            'total_termos_pragas': sum(frequencia_pragas.values()),
            'total_termos_defensivos': sum(frequencia_defensivos.values()),
            'media_pragas_por_registro': round(sum(frequencia_pragas.values()) / total_registros, 2) if total_registros > 0 else 0,
            'media_defensivos_por_registro': round(sum(frequencia_defensivos.values()) / total_registros, 2) if total_registros > 0 else 0
        }
    }

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
            if not all([cultivo, praga, hectares, defensivo, cidade]):
                flash('Todos os campos são obrigatórios!', 'error')
                return render_template('cadastro.html')
            
            hectares_float = float(hectares)
            if hectares_float <= 0:
                flash('Hectares deve ser maior que zero!', 'error')
                return render_template('cadastro.html')
            
            dados_existentes = read_csv()
            novo_id = get_next_id()
            
            novo_registro = {
                'id': novo_id,
                'cultivo': cultivo,
                'praga': praga,
                'hectares': hectares_float,
                'defensivo': defensivo,
                'cidade': cidade,
                'data_cadastro': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
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
        
        dados = read_csv()
        
        dados_filtrados = []
        for registro in dados:
            # Para filtros, também consideramos termos separados por vírgula
            cultivos_registro = processar_termos_separados_por_virgula(registro['cultivo'])
            pragas_registro = processar_termos_separados_por_virgula(registro['praga'])
            cidades_registro = processar_termos_separados_por_virgula(registro['cidade'])
            
            cultivo_match = not filtro_cultivo or any(
                filtro_cultivo.lower() in cultivo.lower() for cultivo in cultivos_registro
            )
            praga_match = not filtro_praga or any(
                filtro_praga.lower() in praga.lower() for praga in pragas_registro
            )
            cidade_match = not filtro_cidade or any(
                filtro_cidade.lower() in cidade.lower() for cidade in cidades_registro
            )
            
            if cultivo_match and praga_match and cidade_match:
                registro_formatado = registro.copy()
                registro_formatado['data_cadastro'] = formatar_data(registro['data_cadastro'])
                dados_filtrados.append(registro_formatado)
        
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
        dados = read_csv()
        dados_atualizados = [row for row in dados if int(row['id']) != id]
        
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
        totais = calcular_totais_frequencias(dados)
        return render_template('estatisticas.html', totais=totais)
        
    except Exception as e:
        flash(f'Erro ao carregar estatísticas: {str(e)}', 'error')
        return render_template('estatisticas.html', totais={})

if __name__ == '__main__':
    init_csv()
    app.run(debug=True)
    