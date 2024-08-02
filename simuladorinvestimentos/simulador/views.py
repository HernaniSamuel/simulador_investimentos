from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
import yfinance as yf
import logging
import json
from .models import Ativo, CarteiraAutomatica, SimulacaoAutomatica
from datetime import datetime, timedelta
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


#@login_required()
@csrf_exempt
def nova_simulacao_automatica(request):
    if request.method == 'POST':
        body = json.loads(request.body)
        nome = body.get('nome')
        data_inicial = body.get('data_inicial') # a data inicial deverá ser corrigida para YYYY-MM-DD
        data_final = body.get('data_final') # a data final deverá ser corrigida para YYYY-MM-DD
        aplicacao_inicial = body.get('aplicacao_inicial')
        aplicacao_mensal = body.get('aplicacao_mensal')
        moeda_base = body.get('moeda_base')

        inflacao_total = pegar_inflacao(start_date=data_inicial, end_date=data_final)

        if not nome or not data_inicial or not data_final or not aplicacao_inicial or not aplicacao_mensal or not moeda_base:
            return JsonResponse({'error': 'Missing parameters'}, status=400)

        carteira_automatica = CarteiraAutomatica.objects.create(
            valor_em_dinheiro=aplicacao_inicial,
            moeda_base=moeda_base
        )

        simulacao_automatica = SimulacaoAutomatica.objects.create(
            nome=nome,
            data_inicial=data_inicial,
            data_final=data_final,
            aplicacao_inicial=aplicacao_inicial,
            aplicacao_mensal=aplicacao_mensal,
            carteira_automatica=carteira_automatica,
            tipo='automatica',
            inflacao_total=inflacao_total
        )
        return JsonResponse({
            'message': 'Simulação automática criada com sucesso',
            'simulacao_id': simulacao_automatica.id,
            'carteira_id': carteira_automatica.id
        }, status=200)

    return JsonResponse({'error': 'Invalid request method'}, status=405)


#@login_required
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

            # Processar os dados recebidos
            for item in data['ativos']:
                ticker = item['ticker']
                peso = item['peso']
                nome = yf.Ticker(ticker).info['longName']
                precos = yf.download(ticker, start=simulacao_automatica.data_inicial, end=simulacao_automatica.data_final, interval='1mo')

                ativo = Ativo.objects.create(
                    ticker=ticker,
                    peso=peso,
                    posse=0,
                    nome=nome,
                    precos=precos,
                    carteira_automatica=carteira_automatica  # Associar o ativo à carteira
                )

            return JsonResponse({'status': 'success'}, status=200)
        except CarteiraAutomatica.DoesNotExist:
            return JsonResponse({'error': 'CarteiraAutomatica not found'}, status=404)
        except SimulacaoAutomatica.DoesNotExist:
            return JsonResponse({'error': 'SimulacaoAutomatica not found'}, status=404)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)


@csrf_exempt
def resultado_simulacao_automatica(request):
    pass
