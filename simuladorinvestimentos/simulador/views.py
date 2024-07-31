from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
import yfinance as yf
import logging
import json
from .models import Ativo, CarteiraAutomatica, SimulacaoAutomatica


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
        data_inicial = body.get('data_inicial')
        data_final = body.get('data_final')
        aplicacao_inicial = body.get('aplicacao_inicial')
        aplicacao_mensal = body.get('aplicacao_mensal')
        moeda_base = body.get('moeda_base')

        if not nome or not data_inicial or not data_final or not aplicacao_inicial or not aplicacao_mensal or not moeda_base:
            return JsonResponse({'error': 'Missing parameters'}, status=400)


        carteira_automatica = CarteiraAutomatica.objects.create(
            valor_em_dinheiro = aplicacao_inicial,
            moeda_base=moeda_base
        )

        simulacao_automatica = SimulacaoAutomatica.objects.create(
            nome=nome,
            data_inicial=data_inicial,
            data_final=data_final,
            aplicacao_inicial=aplicacao_inicial,
            aplicacao_mensal=aplicacao_mensal,
            carteira_automatica=carteira_automatica
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

            def ticker_exists(ticker):
                try:
                    stock = yf.Ticker(ticker)
                    info = stock.info
                    if 'regularMarketPrice' in info:
                        return True
                    else:
                        return False
                except Exception as e:
                    print(f"Error checking ticker: {e}")
                    return False

            if ticker_exists(ticker):
                return JsonResponse({'exists': True, 'ticker': ticker}, status=200)
            else:
                return JsonResponse({'exists': False, 'ticker': ticker}, status=404)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
    return JsonResponse({'error': 'Invalid request method'}, status=405)