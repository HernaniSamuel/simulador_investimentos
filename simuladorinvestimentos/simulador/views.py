import yfinance as yf
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

# imports provisórios
from .models import SimulacaoAutomatica, SimulacaoManual
from .utils import ajustar_inflacao
from datetime import datetime
from dateutil.relativedelta import relativedelta
from .utils import arredondar_para_baixo
import pandas as pd


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


@login_required
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
            # Obtém a simulação pelo ID fornecido
            simulacao_manual = get_object_or_404(SimulacaoManual, id=simulacao_id)


            # Extrai os dados necessários da simulação e dos ativos
            ativos = simulacao_manual.carteira_manual.ativos.all()
            line_data = {
                'valorTotal': [ativo.peso for ativo in ativos],  # Exemplo de valores
                'valorAtivos': [ativo.posse for ativo in ativos],  # Exemplo de valores
            }
            pie_data = [
                {'name': ativo.nome, 'y': ativo.peso} for ativo in ativos
            ]
            cash = simulacao_manual.carteira_manual.valor_em_dinheiro

            # Pega o mês e ano atuais da simulação
            mes_atual = simulacao_manual.mes_atual.strftime('%Y-%m-%d')  # Formata o mês


            # Resposta em formato JSON
            response_data = {
                'lineData': line_data,
                'pieData': pie_data,
                'cash': cash,
                'mes_atual': mes_atual,
            }

            return JsonResponse(response_data, safe=False)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Método inválido. Apenas GET é permitido.'}, status=405)


@login_required
@csrf_exempt
def modificar_dinheiro_view(request, simulacao_id):
    if request.method == 'POST':
        try:
            # Obtém a simulação correspondente
            simulacao = SimulacaoManual.objects.get(id=simulacao_id, usuario=request.user)
            carteira = simulacao.carteira_manual

            # Carrega os dados do POST
            data = json.loads(request.body)
            valor = float(data.get('valor', 0))
            valor = arredondar_para_baixo(valor)
            ajustar_inflacao_flag = data.get('ajustarInflacao', False)

            # Converter JSONField para DataFrame
            ipca_data_json = simulacao.inflacao_total  # Isso é um dicionário
            ipca_data = pd.DataFrame(ipca_data_json)

            # Verificar se 'data' está nas colunas
            if 'Data' in ipca_data.columns:
                # Converter 'data' para datetime e definir como índice
                ipca_data['Data'] = pd.to_datetime(ipca_data['Data'])
                ipca_data.set_index('Data', inplace=True)
            else:
                return JsonResponse({'error': "A coluna 'Data' não está presente em ipca_data."}, status=500)

            # Exibir informações para depuração
            print("ipca_data após ajustes:", ipca_data.head())

            coluna_ipca = "Valor"
            periodo_inicial = datetime.today().date()
            data_final = simulacao.mes_atual.date()

            # Se o valor for 0, não faz nada
            if valor == 0:
                return JsonResponse({'message': 'Nenhuma alteração foi feita, valor 0.'}, status=400)

            # Se o valor de valor_em_dinheiro for None, definimos como 0
            valor_atual_em_dinheiro = carteira.valor_em_dinheiro if carteira.valor_em_dinheiro is not None else 0

            # Se a checkbox estiver marcada, ajusta o valor usando a inflação
            if ajustar_inflacao_flag:
                valor_ajustado = ajustar_inflacao(ipca_data, coluna_ipca, periodo_inicial, valor, data_final)
                if valor_ajustado is None:
                    return JsonResponse({'error': 'Erro ao ajustar o valor pela inflação.'}, status=500)
                valor = arredondar_para_baixo(valor_ajustado)

            # Modifica o valor em caixa da carteira
            novo_valor = max(valor_atual_em_dinheiro + valor, 0)  # Impede valor negativo
            carteira.valor_em_dinheiro = novo_valor
            carteira.save()

            return JsonResponse({'message': 'Valor atualizado com sucesso.', 'novo_valor': novo_valor})

        except SimulacaoManual.DoesNotExist:
            return JsonResponse({'error': 'Simulação não encontrada.'}, status=404)
        except Exception as e:
            print(f"Erro na view modificar_dinheiro: {e}")
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Método inválido. Apenas POST é permitido.'}, status=405)


@login_required
@csrf_exempt
def avancar_mes_view(request, simulacao_id):
    if request.method == 'POST':
        try:
            # Obtém a simulação correspondente
            simulacao = SimulacaoManual.objects.get(id=simulacao_id, usuario=request.user)

            # Adiciona um mês à data atual da simulação
            mes_atual = simulacao.mes_atual
            novo_mes = mes_atual + relativedelta(months=1)

            # Atualiza a simulação com o novo mês
            simulacao.mes_atual = novo_mes
            simulacao.save()

            return JsonResponse({
                'message': 'Simulação avançada para o próximo mês.',
                'mes_atual': novo_mes.strftime('%Y-%m-%d'),  # Formato legível para exibir
            })

        except SimulacaoManual.DoesNotExist:
            return JsonResponse({'error': 'Simulação não encontrada.'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Método inválido. Apenas POST é permitido.'}, status=405)
