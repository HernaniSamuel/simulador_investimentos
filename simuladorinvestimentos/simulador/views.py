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
import yfinance as yf
import pandas as pd


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


@login_required()
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


@login_required()
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
            novo_valor = valor_atual_em_dinheiro + valor

            # Impede que o novo valor seja negativo (mantém pelo menos zero)
            if novo_valor < 0:
                novo_valor = 0

            carteira.valor_em_dinheiro = novo_valor
            carteira.save()

            return JsonResponse({'message': 'Valor atualizado com sucesso.', 'novo_valor': novo_valor})

        except SimulacaoManual.DoesNotExist:
            return JsonResponse({'error': 'Simulação não encontrada.'}, status=404)
        except Exception as e:
            print(f"Erro na view modificar_dinheiro: {e}")
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Método inválido. Apenas POST é permitido.'}, status=405)


@login_required()
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


@login_required
@csrf_exempt
def negociar_ativos_pesquisa(request, simulacao_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método não permitido. Use POST.'}, status=405)

    try:
        # Lê os dados do corpo da requisição
        body = json.loads(request.body)
        print(f"Request body: {body}")  # Log do corpo da requisição
        ticker = body.get('ticker')

        if not ticker:
            print("Erro: Ticker não fornecido.")  # Log de erro
            return JsonResponse({'error': 'Ticker não fornecido.'}, status=400)

        # Obtém a simulação pelo ID fornecido
        print(f"Buscando simulação com ID: {simulacao_id}")  # Log antes de buscar a simulação
        simulacao = get_object_or_404(SimulacaoManual, id=simulacao_id)
        print(f"Simulação encontrada: {simulacao}")  # Log após encontrar a simulação

        # Obtém a data atual da simulação e converte para date se necessário
        data_atual_simulacao = simulacao.mes_atual.date() if isinstance(simulacao.mes_atual, datetime) else simulacao.mes_atual
        print(f"Data atual da simulação: {data_atual_simulacao}")  # Log da data atual

        # Busca o histórico do ativo usando o yfinance
        print(f"Buscando histórico do ativo: {ticker}")  # Log antes de buscar o histórico
        ativo = yf.Ticker(ticker)
        historico = ativo.history(period='max')
        print(f"Histórico obtido para {ticker}: {historico.head()}")  # Log das primeiras linhas do histórico

        if historico.empty:
            print("Histórico vazio para o ticker fornecido.")  # Log se o histórico estiver vazio
            return JsonResponse({'exists': False, 'error': 'Sem histórico de preços para o ticker fornecido.'}, status=404)

        # Pega a primeira data disponível nos dados históricos
        data_inicio_ticker = historico.index[0].date()
        print(f"Data de início do ticker {ticker}: {data_inicio_ticker}")  # Log da data de início do ticker

        # Verifica se a data de início do ativo é anterior ou igual à data atual da simulação
        if data_inicio_ticker <= data_atual_simulacao:
            print(f"O ativo {ticker} existe e tem dados antes da data atual da simulação.")
            return JsonResponse({'exists': True, 'ticker': ticker, 'data_inicio': str(data_inicio_ticker)})
        else:
            print(f"O ativo {ticker} não tem dados antes da data atual da simulação.")
            return JsonResponse({'exists': False, 'ticker': ticker, 'data_inicio': str(data_inicio_ticker)})

    except json.JSONDecodeError:
        print("Erro de JSONDecode: Corpo da requisição inválido.")  # Log de erro de JSON
        return JsonResponse({'error': 'Corpo da requisição inválido. Certifique-se de que está em formato JSON.'}, status=400)
    except Exception as e:
        print(f"Erro inesperado: {str(e)}")  # Log de qualquer outra exceção
        return JsonResponse({'error': f'Ocorreu um erro: {str(e)}'}, status=500)

# Será feita a limpeza do terminal na refatoração views & services


@login_required
@csrf_exempt
def negociar_ativos(request, simulacao_id):
    if request.method == 'POST':
        try:
            # Lê os dados do corpo da requisição
            body = json.loads(request.body)
            print(f"Request body: {body}")
            ticker = body.get('ticker')

            if not ticker:
                print("Erro: Ticker não fornecido.")
                return JsonResponse({'error': 'Ticker não fornecido.'}, status=400)

            # Obtém a simulação manual associada ao ID e ao usuário autenticado
            print(f"Buscando simulação com ID: {simulacao_id}")
            simulacao = get_object_or_404(SimulacaoManual, id=simulacao_id, usuario=request.user)
            carteira_manual = simulacao.carteira_manual

            # Busca o histórico do ativo usando o yfinance
            print(f"Buscando histórico do ativo: {ticker}")
            ativo = yf.Ticker(ticker)
            historico = ativo.history(period='1y')

            # Processa o histórico para o formato esperado pelo gráfico de velas
            historico_lista = [
                {
                    'date': str(index.date()),
                    'open': row['Open'],
                    'high': row['High'],
                    'low': row['Low'],
                    'close': row['Close']
                }
                for index, row in historico.iterrows()
            ]

            # Prepara a resposta com o histórico de preços e o valor disponível em caixa da carteira manual
            response_data = {
                'ticker': ticker,
                'historico': historico_lista,
                'dinheiro_em_caixa': carteira_manual.valor_em_dinheiro
            }

            return JsonResponse(response_data, status=200)

        except json.JSONDecodeError:
            print("Erro de JSONDecode: Corpo da requisição inválido.")
            return JsonResponse({'error': 'Corpo da requisição inválido. Certifique-se de que está em formato JSON.'}, status=400)
        except Exception as e:
            print(f"Erro inesperado: {str(e)}")
            return JsonResponse({'error': f'Ocorreu um erro: {str(e)}'}, status=500)
    else:
        return JsonResponse({'error': 'Método não permitido. Use POST.'}, status=405)
