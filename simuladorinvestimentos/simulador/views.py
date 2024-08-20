from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
import yfinance as yf
import logging
import json
import pandas as pd
from .models import Ativo, CarteiraAutomatica, SimulacaoAutomatica, Historico
from datetime import datetime, timedelta, date
from .utils import pegar_inflacao, ajustar_inflacao


logger = logging.getLogger(__name__)


@login_required()
def index(request):
    return render(request, 'index.html')


@login_required()
@csrf_exempt
def get_data(request):
    if request.method == 'POST':
        body = json.loads(request.body)
        ticker = body.get('ticker')
        start_date = body.get('start_date')
        end_date = body.get('end_date')
        interval = body.get('interval')

        if not ticker or not start_date or not end_date or not interval:
            return JsonResponse({'error': 'Missing parameters'}, status=400)

        data = yf.download(ticker, start=start_date, end=end_date, interval=interval)
        data.reset_index(inplace=True)  # Resetando o índice para que a data esteja disponível como coluna
        data_dict = data.to_dict(orient='records')

        return JsonResponse(data_dict, safe=False)

    return JsonResponse({'error': 'Invalid request method'}, status=405)


@login_required()
@csrf_exempt
def nova_simulacao_automatica(request):
    if request.method == 'POST':
        body = json.loads(request.body)
        nome = body.get('nome')
        data_inicial = body.get('data_inicial')
        data_final = body.get('data_final')
        aplicacao_inicial = body.get('aplicacao_inicial')
        aplicacao_mensal = body.get('aplicacao_mensal')
        moeda_base = body.get('moeda_base')

        if not nome or not data_inicial or not data_final or not aplicacao_inicial or not aplicacao_mensal or not moeda_base:
            return JsonResponse({'error': 'Missing parameters'}, status=400)

        try:
            inflacao_total = pegar_inflacao(start_date=data_inicial, end_date=datetime.today().strftime('%Y-%m-%d'))
            if inflacao_total is None:
                return JsonResponse({'error': 'Failed to fetch inflation data'}, status=500)

            # Convertendo o DataFrame para um formato serializável
            inflacao_total['Data'] = inflacao_total['Data'].dt.strftime('%Y-%m-%d')
            inflacao_dict = inflacao_total.to_dict(orient='records')

            print('Dados de inflação pegos')

            carteira_automatica = CarteiraAutomatica.objects.create(
                valor_em_dinheiro=aplicacao_inicial,
                moeda_base=moeda_base,
                valor_ativos=0
            )
            print('Carteira automática criada')

            simulacao_automatica = SimulacaoAutomatica.objects.create(
                nome=nome,
                data_inicial=data_inicial,
                data_final=data_final,
                aplicacao_inicial=aplicacao_inicial,
                aplicacao_mensal=aplicacao_mensal,
                carteira_automatica=carteira_automatica,
                usuario=request.user,  # Adicionando o usuário à simulação
                inflacao_total=inflacao_dict
            )
            print('Simulação automática criada')

            # Verificar se já existe um histórico para o usuário
            historico, created = Historico.objects.get_or_create(
                usuario=request.user,
                defaults={'data_criacao': datetime.now()}
            )
            print('Histórico criado')

            # Adicionar simulação ao histórico do usuário
            historico.simulacoes.add(simulacao_automatica)
            historico.save()
            print('Simulação adicionada ao histórico')

            return JsonResponse({
                'message': 'Simulação automática criada com sucesso',
                'simulacao_id': simulacao_automatica.id,
                'carteira_id': carteira_automatica.id,
                'inflacao_total': inflacao_dict
            }, status=200)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=405)


@login_required
@csrf_exempt
def pesquisar_ativos(request):
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            ticker = body.get('ticker')

            if not ticker:
                return JsonResponse({'error': 'Ticker is required'}, status=400)

            try:
                stock = yf.Ticker(ticker)
                stock_info = stock.info

                # Verificando se o ticker é válido
                if 'longName' in stock_info:
                    stock_name = stock_info['longName']
                else:
                    stock_name = 'Unknown'

                # Baixando os dados históricos do ticker
                end_date = datetime.now().strftime('%Y-%m-%d')
                start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

                # Baixa os dados do ativo
                stock_data = yf.download(ticker, start=start_date, end=end_date, interval='1mo')

                # Verificando se há dados retornados
                if not stock_data.empty:
                    adj_close = stock_data['Adj Close'].iloc[0]  # Obtendo o primeiro valor de 'Adj Close'
                    if adj_close > 0:
                        return JsonResponse({'exists': True, 'ticker': ticker, 'name': stock_name}, status=200)
                    else:
                        return JsonResponse({'exists': False, 'ticker': ticker, 'name': stock_name}, status=404)
                else:
                    return JsonResponse({'exists': False, 'ticker': ticker, 'name': stock_name}, status=404)
            except Exception as e:
                print(f"Error checking ticker: {e}")
                return JsonResponse({'exists': False, 'ticker': ticker}, status=404)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
    return JsonResponse({'error': 'Invalid request method'}, status=405)


@login_required()
@csrf_exempt
def enviar_ativos(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            carteira_id = data.get('carteira_id')
            simulacao_id = data.get('simulacao_id')

            if not carteira_id or not simulacao_id:
                return JsonResponse({'error': 'Missing carteira_id or simulacao_id'}, status=400)

            carteira_automatica = CarteiraAutomatica.objects.get(id=carteira_id)
            simulacao_automatica = SimulacaoAutomatica.objects.get(id=simulacao_id)

            moeda_carteira = carteira_automatica.moeda_base

            # Dicionário para armazenar as taxas de câmbio baixadas
            cambio_cache = {}

            for item in data['ativos']:
                ticker = item['ticker']
                peso = item['peso']
                print(f"Processando ativo: {ticker} com peso {peso}")

                # Obtendo informações do ativo
                ativo_info = yf.Ticker(ticker).info
                nome = ativo_info['longName']
                moeda_ativo = ativo_info['currency']

                # Pegar preços dos ativos
                precos_df = yf.download(ticker, start=simulacao_automatica.data_inicial,
                                        end=simulacao_automatica.data_final, interval='1mo')

                # Se a moeda do ativo for diferente da moeda da carteira, faça a conversão
                if moeda_ativo != moeda_carteira:
                    print(f"Convertendo preços de {moeda_ativo} para {moeda_carteira}")

                    # Verificar se o câmbio já está no cache
                    if moeda_ativo in cambio_cache:
                        cambio_df = cambio_cache[moeda_ativo]
                    else:
                        cambio_ticker = f"{moeda_ativo}{moeda_carteira}=X"
                        cambio_df = yf.download(cambio_ticker, start=simulacao_automatica.data_inicial,
                                                end=simulacao_automatica.data_final, interval='1mo')
                        cambio_cache[moeda_ativo] = cambio_df  # Armazenar no cache

                    # Garantindo que a data do câmbio corresponde à data dos preços do ativo
                    cambio_df = cambio_df.reindex(precos_df.index, method='ffill')

                    # Convertendo preços para a moeda da carteira
                    precos_df['Adj Close'] = precos_df['Adj Close'] * cambio_df['Adj Close']

                # Converter DataFrame para lista de dicionários com datas como strings
                precos = precos_df.reset_index().to_dict(orient='records')
                for preco in precos:
                    preco['Date'] = preco['Date'].isoformat()  # Converter Timestamp para string ISO 8601

                print(f"Criando objeto Ativo para {ticker}")
                ativo = Ativo.objects.create(
                    ticker=ticker,
                    peso=peso,
                    posse=0,
                    nome=nome,
                    precos=json.dumps(precos),  # Serializar para JSON
                )

                carteira_automatica.ativos.add(ativo)

            return JsonResponse({'status': 'success'}, status=200)
        except CarteiraAutomatica.DoesNotExist:
            return JsonResponse({'error': 'CarteiraAutomatica not found'}, status=404)
        except SimulacaoAutomatica.DoesNotExist:
            return JsonResponse({'error': 'SimulacaoAutomatica not found'}, status=404)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)

"""
@login_required()
@csrf_exempt
def resultado_simulacao_automatica(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            simulacao_id = data.get('simulacao_id')

            if not simulacao_id:
                return JsonResponse({'error': 'Missing simulacao_id'}, status=400)

            simulacao = SimulacaoAutomatica.objects.get(id=simulacao_id)

            ipca_data = pd.DataFrame(simulacao.inflacao_total)
            ipca_data['Data'] = pd.to_datetime(ipca_data['Data'], format='%Y-%m-%d')
            ipca_data.set_index('Data', inplace=True)

            data_inicial = pd.to_datetime(simulacao.data_inicial)
            data_final = pd.to_datetime(simulacao.data_final)

            if data_inicial is None or data_final is None:
                return JsonResponse({'error': 'Invalid date format'}, status=400)

            aplicacao_inicial_ajustada = ajustar_inflacao(
                periodo_inicial=data_inicial,
                ipca_data=ipca_data,
                coluna_ipca='Valor',
                valor=simulacao.aplicacao_inicial,
                data_final=data_final
            ) or 0

            aplicacoes_mensais_ajustadas = []
            datas_validas = ipca_data.loc[(ipca_data.index >= data_inicial) & (ipca_data.index <= data_final)].index
            for data_corrente in datas_validas:
                aplicacao_mensal_ajustada = ajustar_inflacao(
                    periodo_inicial=data_corrente,
                    ipca_data=ipca_data,
                    coluna_ipca='Valor',
                    valor=simulacao.aplicacao_mensal,
                    data_final=data_final
                ) or 0
                aplicacoes_mensais_ajustadas.append(aplicacao_mensal_ajustada)

            ativos = list(simulacao.carteira_automatica.ativos.all())
            adjclose_carteira = []
            valor_total_carteira = aplicacao_inicial_ajustada

            for mes_index, (data_corrente, aplicacao_mensal) in enumerate(
                    zip(datas_validas, aplicacoes_mensais_ajustadas)):
                valor_total_carteira += aplicacao_mensal
                for ativo in ativos:
                    precos = json.loads(ativo.precos)
                    if mes_index < len(precos):
                        preco_ativo = precos[mes_index]['Adj Close']
                        valor_investido = aplicacao_mensal * ativo.peso
                        quantidade_comprada = valor_investido / preco_ativo if preco_ativo > 0 else 0
                        ativo.posse += quantidade_comprada
                        valor_total_carteira -= valor_investido

                        if preco_ativo <= 0:
                            print(f"Alerta: Preço zero ou negativo detectado para {ativo.nome} no mês {mes_index}")

                valor_total_carteira_mes = sum(
                    a.posse * json.loads(a.precos)[mes_index]['Adj Close']
                    for a in ativos
                    if mes_index < len(json.loads(a.precos))
                )
                adjclose_carteira.append((data_corrente, valor_total_carteira_mes))

            # remover último mês zerado (medida provisória até a refatoração)
            if adjclose_carteira:
                adjclose_carteira.pop()

            # Criar um DataFrame com as datas e valores correspondentes
            df_resultado = pd.DataFrame(adjclose_carteira, columns=['Data', 'Valor'])

            # Save changes if necessary
            for ativo in ativos:
                ativo.save()

            return JsonResponse({'adjclose_carteira': df_resultado.to_dict(orient='records')}, status=200)

        except SimulacaoAutomatica.DoesNotExist:
            return JsonResponse({'error': 'SimulacaoAutomatica not found'}, status=404)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            print(f'Erro durante a simulação: {str(e)}')
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=405)
"""


@login_required()
@csrf_exempt
def resultado_simulacao_automatica(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            simulacao_id = data.get('simulacao_id')

            if not simulacao_id:
                return JsonResponse({'error': 'Missing simulacao_id'}, status=400)

            simulacao = SimulacaoAutomatica.objects.get(id=simulacao_id)

            ipca_data = pd.DataFrame(simulacao.inflacao_total)
            ipca_data['Data'] = pd.to_datetime(ipca_data['Data'], format='%Y-%m-%d')
            ipca_data.set_index('Data', inplace=True)

            data_inicial = pd.to_datetime(simulacao.data_inicial)
            data_final = pd.to_datetime(simulacao.data_final)

            if data_inicial is None or data_final is None:
                return JsonResponse({'error': 'Invalid date format'}, status=400)

            # Adicionando um mês ao período final
            data_final_extendida = data_final + pd.DateOffset(months=1)

            aplicacao_inicial_ajustada = ajustar_inflacao(
                periodo_inicial=data_inicial,
                ipca_data=ipca_data,
                coluna_ipca='Valor',
                valor=simulacao.aplicacao_inicial,
                data_final=data_final_extendida
            ) or 0

            aplicacoes_mensais_ajustadas = []
            datas_validas = ipca_data.loc[
                (ipca_data.index >= data_inicial) & (ipca_data.index <= data_final_extendida)].index
            for data_corrente in datas_validas:
                aplicacao_mensal_ajustada = ajustar_inflacao(
                    periodo_inicial=data_corrente,
                    ipca_data=ipca_data,
                    coluna_ipca='Valor',
                    valor=simulacao.aplicacao_mensal,
                    data_final=data_final_extendida
                ) or 0
                aplicacoes_mensais_ajustadas.append(aplicacao_mensal_ajustada)

            ativos = list(simulacao.carteira_automatica.ativos.all())
            adjclose_carteira = []
            valor_total_carteira = aplicacao_inicial_ajustada

            for mes_index, (data_corrente, aplicacao_mensal) in enumerate(
                    zip(datas_validas, aplicacoes_mensais_ajustadas)):
                valor_total_carteira += aplicacao_mensal
                for ativo in ativos:
                    precos = json.loads(ativo.precos)
                    if mes_index < len(precos):
                        preco_ativo = precos[mes_index]['Adj Close']
                        valor_investido = aplicacao_mensal * ativo.peso
                        quantidade_comprada = valor_investido / preco_ativo if preco_ativo > 0 else 0
                        ativo.posse += quantidade_comprada
                        valor_total_carteira -= valor_investido

                        if preco_ativo <= 0:
                            print(f"Alerta: Preço zero ou negativo detectado para {ativo.nome} no mês {mes_index}")

                valor_total_carteira_mes = sum(
                    a.posse * json.loads(a.precos)[mes_index]['Adj Close']
                    for a in ativos
                    if mes_index < len(json.loads(a.precos))
                )
                adjclose_carteira.append((data_corrente, valor_total_carteira_mes))

            # Criar um DataFrame com as datas e valores correspondentes
            df_resultado = pd.DataFrame(adjclose_carteira, columns=['Data', 'Valor'])

            # Coletar informações dos ativos
            ativos_info = [
                {
                    'nome': ativo.nome,
                    'ticker': ativo.ticker,
                    'peso': ativo.peso,
                    'posse': ativo.posse
                }
                for ativo in ativos
            ]

            # Estruturar a resposta JSON
            resposta = {
                'simulacao': {
                    'valor_inicial': simulacao.aplicacao_inicial,
                    'valor_mensal': simulacao.aplicacao_mensal,
                    'data_inicial': simulacao.data_inicial,
                    'data_final': simulacao.data_final,
                    'ativos': ativos_info
                },
                'resultado': df_resultado.to_dict(orient='records')
            }

            # Save changes if necessary
            for ativo in ativos:
                ativo.save()

            return JsonResponse(resposta, status=200)

        except SimulacaoAutomatica.DoesNotExist:
            return JsonResponse({'error': 'SimulacaoAutomatica not found'}, status=404)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            print(f'Erro durante a simulação: {str(e)}')
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=405)

def safe_strptime(date_str, format='%Y-%m-%d'):
    try:
        return datetime.strptime(date_str, format).date()
    except ValueError:
        return None


@login_required()
@csrf_exempt
def listar_historico(request):
    if request.method == 'GET':
        historico = Historico.objects.filter(usuario=request.user)
        historico_list = [
            {
                'id': item.id,
                'simulacoes': [
                    {
                        'simulacao_id': simulacao.id,
                        'nome': simulacao.nome,
                        'data_criacao': item.data_criacao,
                        'data_inicial': simulacao.data_inicial,
                        'data_final': simulacao.data_final,
                        'aplicacao_inicial': simulacao.aplicacao_inicial,
                        'aplicacao_mensal': simulacao.aplicacao_mensal,
                    }
                    for simulacao in item.simulacoes.all()
                ]
            }
            for item in historico
        ]
        return JsonResponse(historico_list, safe=False)
    return JsonResponse({'error': 'Invalid request method'}, status=405)


@login_required()
@csrf_exempt
def excluir_simulacao(request, simulacao_id):
    simulacao = get_object_or_404(SimulacaoAutomatica, id=simulacao_id, usuario=request.user)
    simulacao.delete()
    return JsonResponse({'message': 'Simulação excluída com sucesso'})
