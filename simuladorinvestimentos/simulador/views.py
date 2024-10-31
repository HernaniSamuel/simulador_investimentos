import logging
import json

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt

from .services.nova_simulacao_automatica_services import criar_simulacao_automatica
from .services.nova_simulacao_manual_services import criar_simulacao_manual
from .services.pesquisar_ativos_services import pesquisar_ativo_por_ticker
from .services.enviar_ativos_services import enviar_ativos_para_carteira
from .services.resultado_simulacao_automatica_services import calcular_resultado_simulacao
from .services.listar_historico_services import obter_historico_usuario
from .services.abrir_simulacao_automatica_services import processar_simulacao_automatica
from .services.simulacao_manual_services import calcular_simulacao_manual
from .services.modificar_dinheiro_services import modificar_dinheiro
from .services.avancar_mes_services import avancar_mes
from .services.negociar_ativos_pesquisa_services import pesquisar_ativo
from .services.negociar_ativos_services import negociar_ativo
from .services.buy_sell_actives_services import processar_compra_venda

from .models import SimulacaoAutomatica, SimulacaoManual


logger = logging.getLogger(__name__)


@login_required()
def index(request):
    return render(request, 'index.html')


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
            simulacao_automatica, carteira_automatica = criar_simulacao_automatica(
                nome, data_inicial, data_final, aplicacao_inicial, aplicacao_mensal, moeda_base, request.user
            )

            return JsonResponse({
                'message': 'Simulação automática criada com sucesso',
                'simulacao_id': simulacao_automatica.id,
                'carteira_id': carteira_automatica.id
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
def abrir_simulacao_automatica(request):
    if request.method == 'POST':
        try:
            # Carregar o corpo da requisição como JSON
            body = json.loads(request.body)
            simulacao_id = body.get('simulacao_id')

            if not simulacao_id:
                return JsonResponse({'error': 'Simulacao ID is required'}, status=400)

            # Chama a função de serviço para processar a simulação
            resposta, status_code = processar_simulacao_automatica(simulacao_id)

            return JsonResponse(resposta, status=status_code)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

    return JsonResponse({'error': 'Invalid request method'}, status=405)


@login_required()
@csrf_exempt
def excluir_simulacao_automatica(request, simulacao_id):
    simulacao = get_object_or_404(SimulacaoAutomatica, id=simulacao_id, usuario=request.user)
    simulacao.delete()
    return JsonResponse({'message': 'Simulação excluída com sucesso'})


@login_required()
@csrf_exempt
def excluir_simulacao_manual(request, simulacao_id):
    simulacao = get_object_or_404(SimulacaoManual, id=simulacao_id, usuario=request.user)
    simulacao.delete()
    return JsonResponse({'message': 'Simulação excluída com sucesso'})


@login_required()
@csrf_exempt
def nova_simulacao_manual(request):
    if request.method == 'POST':
        body = json.loads(request.body)
        nome = body.get('nome')
        data_inicial = body.get('data_inicial')
        moeda_base = body.get('moeda_base')

        if not all([nome, data_inicial, moeda_base]):
            return JsonResponse({'error': 'Missing parameters'}, status=400)

        try:
            simulacao_manual, carteira_manual = criar_simulacao_manual(
                nome, data_inicial, moeda_base, request.user
            )
            print(f'Simulação manual criada e registrada! {simulacao_manual.id}')
            return JsonResponse({
                'message': 'Simulação manual criada com sucesso',
                'simulacao_id': simulacao_manual.id,
                'carteira_id': carteira_manual.id
            }, status=200)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=405)


@login_required
@csrf_exempt
def simulacao_manual(request, simulacao_id):
    if request.method == 'GET':
        try:
            # Chamada ao serviço que contém a lógica de simulação
            response_data = calcular_simulacao_manual(simulacao_id)
            return JsonResponse(response_data, safe=False)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Método inválido. Apenas GET é permitido.'}, status=405)


@login_required
@csrf_exempt
def modificar_dinheiro_view(request, simulacao_id):
    if request.method == 'POST':
        try:
            # Carrega os dados do POST
            data = json.loads(request.body)
            valor = float(data.get('valor', 0))
            ajustar_inflacao_flag = data.get('ajustarInflacao', False)

            # Chamada ao serviço que contém a lógica
            response_data, status_code = modificar_dinheiro(simulacao_id, request.user, valor, ajustar_inflacao_flag)
            return JsonResponse(response_data, status=status_code)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'JSON inválido.'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Método inválido. Apenas POST é permitido.'}, status=405)


@login_required
@csrf_exempt
def avancar_mes_view(request, simulacao_id):
    if request.method == 'POST':
        try:
            # Chama o serviço para avançar o mês
            response_data, status_code = avancar_mes(simulacao_id, request.user)
            return JsonResponse(response_data, status=status_code)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Método inválido. Apenas POST é permitido.'}, status=405)


@login_required
@csrf_exempt
def negociar_ativos_pesquisa(request, simulacao_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método não permitido. Use POST.'}, status=405)

    try:
        # Lê os dados do corpo da requisição
        body = json.loads(request.body)
        ticker = body.get('ticker')

        if not ticker:
            return JsonResponse({'error': 'Ticker não fornecido.'}, status=400)

        # Chama o serviço para pesquisar o ativo
        response_data, status_code = pesquisar_ativo(ticker, simulacao_id)
        return JsonResponse(response_data, status=status_code)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Corpo da requisição inválido. Certifique-se de que está em formato JSON.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'Ocorreu um erro: {str(e)}'}, status=500)


@login_required
@csrf_exempt
def negociar_ativos(request, simulacao_id):
    if request.method == 'POST':
        try:
            # Lê os dados do corpo da requisição
            body = json.loads(request.body)
            ticker = body.get('ticker')

            if not ticker:
                return JsonResponse({'error': 'Ticker não fornecido.'}, status=400)

            # Chama o serviço para processar a negociação
            response_data, status_code = negociar_ativo(simulacao_id, request.user, ticker)
            return JsonResponse(response_data, status=status_code)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Corpo da requisição inválido. Certifique-se de que está em formato JSON.'}, status=400)
        except Exception as e:
            return JsonResponse({'error': f'Ocorreu um erro: {str(e)}'}, status=500)

    else:
        return JsonResponse({'error': 'Método não permitido. Use POST.'}, status=405)


@login_required
@csrf_exempt
def buy_sell_actives(request, simulacao_id):
    if request.method == 'POST':
        try:
            # Lê os dados do corpo da requisição
            body = json.loads(request.body)
            tipo_operacao = body.get('tipo')  # 'compra' ou 'venda'
            valor = float(body.get('valor'))  # Valor de compra ou venda
            preco_convertido = float(body.get('precoConvertido'))  # Preço convertido do ativo
            ticker = body.get('ticker')  # Ticker do ativo

            if not tipo_operacao or valor <= 0 or not ticker:
                return JsonResponse({'error': 'Operação inválida ou dados incompletos.'}, status=400)

            # Chama o serviço para processar a compra ou venda
            response_data, status_code = processar_compra_venda(simulacao_id, request.user, tipo_operacao, valor, preco_convertido, ticker)
            return JsonResponse(response_data, status=status_code)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Corpo da requisição inválido. Certifique-se de que está em formato JSON.'}, status=400)
        except Exception as e:
            return JsonResponse({'error': f'Erro inesperado: {str(e)}'}, status=500)

    else:
        return JsonResponse({'error': 'Método não permitido. Use POST.'}, status=405)
