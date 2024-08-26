import yfinance as yf
import logging
import json

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt

from .models import SimulacaoAutomatica

from .services.nova_simulacao_automatica_services import criar_simulacao_automatica
from .services.pesquisar_ativos_services import pesquisar_ativo_por_ticker
from .services.enviar_ativos_services import enviar_ativos_para_carteira
from .services.resultado_simulacao_automatica_services import calcular_resultado_simulacao
from .services.listar_historico_services import obter_historico_usuario


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

        if not all([nome, data_inicial, data_final, aplicacao_inicial, aplicacao_mensal, moeda_base]):
            return JsonResponse({'error': 'Missing parameters'}, status=400)

        try:
            simulacao_automatica, carteira_automatica, inflacao_dict = criar_simulacao_automatica(
                nome, data_inicial, data_final, aplicacao_inicial, aplicacao_mensal, moeda_base, request.user
            )

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

            response_data, status_code = pesquisar_ativo_por_ticker(ticker)
            return JsonResponse(response_data, status=status_code)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

    return JsonResponse({'error': 'Invalid request method'}, status=405)


@login_required()
@csrf_exempt
def enviar_ativos(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            response_data, status_code = enviar_ativos_para_carteira(data)
            return JsonResponse(response_data, status=status_code)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

    return JsonResponse({'error': 'Invalid request method'}, status=405)


@login_required()
@csrf_exempt
def resultado_simulacao_automatica(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            simulacao_id = data.get('simulacao_id')

            if not simulacao_id:
                return JsonResponse({'error': 'Missing simulacao_id'}, status=400)

            response_data, status_code = calcular_resultado_simulacao(simulacao_id)
            return JsonResponse(response_data, status=status_code)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

    return JsonResponse({'error': 'Invalid request method'}, status=405)


@login_required()
@csrf_exempt
def listar_historico(request):
    if request.method == 'GET':
        historico_list = obter_historico_usuario(request.user)
        return JsonResponse(historico_list, safe=False)
    return JsonResponse({'error': 'Invalid request method'}, status=405)


@login_required()
@csrf_exempt
def excluir_simulacao(request, simulacao_id):
    simulacao = get_object_or_404(SimulacaoAutomatica, id=simulacao_id, usuario=request.user)
    simulacao.delete()
    return JsonResponse({'message': 'Simulação excluída com sucesso'})
