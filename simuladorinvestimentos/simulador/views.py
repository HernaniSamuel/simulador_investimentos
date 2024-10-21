import logging
import json

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone

from .services.nova_simulacao_automatica_services import criar_simulacao_automatica
from .services.nova_simulacao_manual_services import criar_simulacao_manual
from .services.pesquisar_ativos_services import pesquisar_ativo_por_ticker
from .services.enviar_ativos_services import enviar_ativos_para_carteira
from .services.resultado_simulacao_automatica_services import calcular_resultado_simulacao
from .services.listar_historico_services import obter_historico_usuario
from .services.abrir_simulacao_automatica_services import processar_simulacao_automatica

# imports provisórios
from .models import SimulacaoAutomatica, SimulacaoManual, Ativo
from .utils import ajustar_inflacao, arredondar_para_baixo
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
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
            simulacao_manual = get_object_or_404(SimulacaoManual, id=simulacao_id)
            ativos = simulacao_manual.carteira_manual.ativos.filter(posse__gt=0)
            valor_total_ativos = 0
            soma_ponderada_posses_precos = 0
            pie_data = []
            line_data = {
                'valorTotal': simulacao_manual.historico_valor_total or [],
                'valorAtivos': [],
            }
            mes_atual = simulacao_manual.mes_atual.strftime('%Y-%m-%d')

            for ativo in ativos:
                precos_armazenados = ativo.precos
                if precos_armazenados:
                    ultimo_preco_data = list(precos_armazenados.values())[-1]
                    ultimo_preco = ultimo_preco_data.get('close', 0)
                else:
                    ultimo_preco = 0
                valor_ativo = ativo.posse * ultimo_preco
                valor_total_ativos += valor_ativo
                soma_ponderada_posses_precos += valor_ativo
                line_data['valorAtivos'].append(ativo.posse)

            for ativo in ativos:
                precos_armazenados = ativo.precos
                if precos_armazenados:
                    ultimo_preco_data = list(precos_armazenados.values())[-1]
                    ultimo_preco = ultimo_preco_data.get('close', 0)
                else:
                    ultimo_preco = 0
                peso_ativo = (ativo.posse * ultimo_preco) / soma_ponderada_posses_precos if soma_ponderada_posses_precos > 0 else 0
                pie_data.append({
                    'name': ativo.nome,
                    'y': round(peso_ativo * 100, 2)
                })

            cash = simulacao_manual.carteira_manual.valor_em_dinheiro

            response_data = {
                'nome_simulacao': simulacao_manual.nome,
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


@login_required
@csrf_exempt
def avancar_mes_view(request, simulacao_id):
    if request.method == 'POST':
        try:
            # Obtém a simulação e a carteira associada
            simulacao = get_object_or_404(SimulacaoManual, id=simulacao_id, usuario=request.user)
            carteira_manual = simulacao.carteira_manual

            # Define o mês atual e o novo mês
            mes_atual = simulacao.mes_atual
            novo_mes = mes_atual + relativedelta(months=1)

            # Processa cada ativo na carteira
            ativos = carteira_manual.ativos.all()
            for ativo in ativos:
                try:
                    yf_data = yf.Ticker(ativo.ticker)

                    # Ajusta as datas para incluir o mês atual
                    historico_precos = yf_data.history(
                        start=mes_atual.strftime('%Y-%m-%d'),
                        end=novo_mes.strftime('%Y-%m-%d'),  # 'end' é exclusivo
                        interval="1mo",
                        auto_adjust=False,  # Obtém preços não ajustados
                        actions=True       # Garante que os dados de dividendos sejam obtidos
                    )

                    if not historico_precos.empty:
                        # Formata o histórico de preços para o mês atual
                        novo_preco = {
                            str(index.date()): {
                                'open': float(row['Open']),
                                'high': float(row['High']),
                                'low': float(row['Low']),
                                'close': float(row['Close'])
                            }
                            for index, row in historico_precos.iterrows()
                        }

                        # Atualiza os preços no ativo
                        ativo.precos.update(novo_preco)
                        ativo.save()
                    else:
                        print(f"{ativo.ticker}: No price data found for {mes_atual.strftime('%Y-%m')}.")

                    # Processa os dividendos para o mês atual
                    dividendos = yf_data.dividends
                    if not dividendos.empty:
                        # Filtra os dividendos no mês atual
                        dividendos_mes = dividendos.loc[(dividendos.index >= mes_atual) & (dividendos.index < novo_mes)]
                        if not dividendos_mes.empty:
                            # Calcula o total de dividendos recebidos
                            total_dividendo = dividendos_mes.sum() * ativo.posse
                            total_dividendo_arredondado = arredondar_para_baixo(total_dividendo)

                            # Atualiza o valor em dinheiro na carteira
                            carteira_manual.valor_em_dinheiro += total_dividendo_arredondado
                            carteira_manual.save()

                except Exception as e:
                    print(f"Erro ao processar ativo {ativo.ticker}: {e}")

            # Recalcula o valor total dos ativos após atualizar os preços
            ativos = carteira_manual.ativos.filter(posse__gt=0)
            valor_total_ativos = 0
            for ativo in ativos:
                precos_armazenados = ativo.precos
                mes_str = mes_atual.strftime('%Y-%m-%d')  # Usamos 'mes_atual' aqui
                preco_no_mes_data = precos_armazenados.get(mes_str, None)
                if preco_no_mes_data:
                    preco_no_mes = preco_no_mes_data.get('close', 0)
                else:
                    preco_no_mes = 0
                valor_ativo = ativo.posse * preco_no_mes
                valor_total_ativos += valor_ativo

            # Atualiza o histórico de valor total
            historico = simulacao.historico_valor_total or []
            historico.append(valor_total_ativos)
            simulacao.historico_valor_total = historico

            # Atualiza a simulação para o novo mês
            simulacao.mes_atual = novo_mes
            simulacao.save()

            return JsonResponse({
                'message': 'Simulação avançada para o próximo mês.',
                'mes_atual': novo_mes.strftime('%Y-%m-%d'),
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

        # Busca o histórico do ativo usando o yfinance com preços não ajustados
        print(f"Buscando histórico do ativo: {ticker}")  # Log antes de buscar o histórico
        ativo = yf.Ticker(ticker)
        historico = ativo.history(period='max', auto_adjust=False)
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
            ticker = body.get('ticker')

            if not ticker:
                return JsonResponse({'error': 'Ticker não fornecido.'}, status=400)

            # Inicializa o objeto ativo no yfinance
            ativo = yf.Ticker(ticker)

            # Obtém a moeda do ativo (por exemplo, USD, BRL, etc.)
            moeda_ativo = ativo.info.get('currency', 'USD')

            # Obtém a simulação manual associada ao ID e ao usuário autenticado
            simulacao = get_object_or_404(SimulacaoManual, id=simulacao_id, usuario=request.user)
            carteira_manual = simulacao.carteira_manual

            # Obter 'mes_atual' da simulação
            mes_atual = simulacao.mes_atual

            # Tornar 'mes_atual' "aware" se for "naive"
            if timezone.is_naive(mes_atual):
                mes_atual = timezone.make_aware(mes_atual, timezone.get_default_timezone())

            # Calcular a data de início (um ano antes de 'mes_atual')
            data_inicio = mes_atual - timedelta(days=365)

            # Verificar se o ativo está na carteira do usuário e obter a quantidade de posse
            ativo_na_carteira = carteira_manual.ativos.filter(ticker=ticker).first()

            # Se o ativo estiver na carteira, usa os preços armazenados
            if ativo_na_carteira and ativo_na_carteira.precos:
                # Usar os preços armazenados
                precos_armazenados = ativo_na_carteira.precos

                # Filtrar os preços dentro do intervalo de datas
                historico_lista = [
                    {
                        'date': data,
                        'open': preco['open'],
                        'high': preco['high'],
                        'low': preco['low'],
                        'close': preco['close']
                    }
                    for data, preco in precos_armazenados.items()
                    if data_inicio.date() <= datetime.strptime(data, '%Y-%m-%d').date() <= mes_atual.date()
                ]

                # Ordenar o histórico por data
                historico_lista.sort(key=lambda x: datetime.strptime(x['date'], '%Y-%m-%d'))

                # Ordenar as datas para obter o último preço
                sorted_dates = sorted(precos_armazenados.keys(), key=lambda date: datetime.strptime(date, '%Y-%m-%d'))

                # Obter o último preço de fechamento
                ultimo_preco_data = sorted_dates[-1]  # Data mais recente
                ultimo_preco_dict = precos_armazenados[ultimo_preco_data]  # Dicionário OHLC
                ultimo_preco = float(ultimo_preco_dict['close'])  # Preço de fechamento

            else:
                # Se não houver preços armazenados, faça a requisição externa ao yfinance
                # Ajuste aqui: Obter preços não ajustados e garantir que dados de dividendos estejam disponíveis
                historico = ativo.history(
                    start=data_inicio.strftime('%Y-%m-%d'),
                    end=mes_atual.strftime('%Y-%m-%d'),
                    auto_adjust=False,  # Obtém preços não ajustados
                    actions=True        # Garante que dados de dividendos estejam disponíveis
                )

                if historico.empty:
                    return JsonResponse({'error': 'Não há dados históricos para o período especificado.'}, status=404)

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

                # Obtém o último preço de fechamento
                ultimo_preco = float(historico['Close'].iloc[-1])

                # Armazena os preços no ativo se desejar reutilizá-los no futuro
                precos = {
                    str(index.date()): {
                        'open': float(row['Open']),
                        'high': float(row['High']),
                        'low': float(row['Low']),
                        'close': float(row['Close'])
                    }
                    for index, row in historico.iterrows()
                }

                # Se desejar salvar o ativo na carteira com os preços, pode fazê-lo aqui
                # Exemplo (opcional):
                # novo_ativo = Ativo.objects.create(
                #     ticker=ticker,
                #     nome=ticker,
                #     peso=0.0,
                #     posse=0.0,
                #     precos=precos,
                #     data_lancamento=None
                # )
                # carteira_manual.ativos.add(novo_ativo)
                # carteira_manual.save()

            # Conversão de moeda
            moeda_carteira = carteira_manual.moeda_base  # Moeda da carteira

            # Se a moeda do ativo for diferente da moeda da carteira, faz a conversão
            if moeda_ativo != moeda_carteira:
                # Obtém a taxa de câmbio com base no mes_atual
                conversao_ticker = f"{moeda_ativo}{moeda_carteira}=X"  # Exemplo: 'USDBRL=X'
                # Ajuste aqui: Obter preços não ajustados para a taxa de câmbio
                historico_conversao = yf.Ticker(conversao_ticker).history(
                    start=data_inicio.strftime('%Y-%m-%d'),
                    end=mes_atual.strftime('%Y-%m-%d'),
                    auto_adjust=False,
                    actions=False
                )

                # Se não houver dados de conversão, usar taxa de 1:1 e informar o usuário
                if historico_conversao.empty:
                    taxa_conversao = 1  # Define taxa de conversão como 1:1
                else:
                    taxa_conversao = historico_conversao['Close'].iloc[-1]
                    taxa_conversao = float(taxa_conversao)

                # Converte o preço do ativo
                ultimo_preco_convertido = ultimo_preco * taxa_conversao
            else:
                ultimo_preco_convertido = ultimo_preco  # Já está na moeda correta

            # Calcula a posse do ativo se ele estiver na carteira
            if ativo_na_carteira:
                quantidade_ativo = ativo_na_carteira.posse  # Obtém a quantidade de posse do ativo
                valor_posse = quantidade_ativo * ultimo_preco_convertido  # Calcula o valor da posse
            else:
                quantidade_ativo = 0
                valor_posse = 0

            # Prepara a resposta com o histórico de preços, valor em caixa, quantidade do ativo na carteira e nome da simulação
            response_data = {
                'ticker': ticker,
                'historico': historico_lista,
                'dinheiro_em_caixa': carteira_manual.valor_em_dinheiro,
                'preco_convertido': ultimo_preco_convertido,
                'moeda_ativo': moeda_ativo,
                'moeda_carteira': moeda_carteira,
                'quantidade_ativo': quantidade_ativo,
                'valor_posse': valor_posse,  # Valor que o usuário possui do ativo
                'ultimo_preco': ultimo_preco,  # Último preço do ativo
                'nome_simulacao': simulacao.nome  # Nome da simulação
            }

            return JsonResponse(response_data, status=200)

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
            print("[DEBUG] Início da função buy_sell_actives")
            # Lê os dados da requisição
            body = json.loads(request.body)
            print(f"[DEBUG] Corpo da requisição: {body}")
            tipo_operacao = body.get('tipo')  # 'compra' ou 'venda'
            valor = float(body.get('valor'))  # Valor de compra ou venda em moeda da carteira
            preco_convertido = float(body.get('precoConvertido'))  # Preço convertido do ativo
            ticker = body.get('ticker')  # Ticker do ativo sendo negociado

            print(f"[DEBUG] tipo_operacao: {tipo_operacao}, valor: {valor}, preco_convertido: {preco_convertido}, ticker: {ticker}")

            if not tipo_operacao or valor <= 0:
                print("[ERROR] Operação inválida ou valor menor ou igual a zero.")
                return JsonResponse({'error': 'Operação inválida ou valor menor ou igual a zero.'}, status=400)

            if not ticker:
                print("[ERROR] Ticker não fornecido.")
                return JsonResponse({'error': 'Ticker não fornecido.'}, status=400)

            # Obtenha a simulação manual e a carteira associada
            simulacao = get_object_or_404(SimulacaoManual, id=simulacao_id, usuario=request.user)
            carteira_manual = simulacao.carteira_manual

            print(f"[DEBUG] Simulação ID: {simulacao_id}, Carteira Manual ID: {carteira_manual.id}")

            # Verifica se o ativo já existe na carteira dessa simulação
            ativo_na_carteira = carteira_manual.ativos.filter(ticker=ticker).first()
            print(f"[DEBUG] Ativo na carteira: {ativo_na_carteira}")

            # Caso o ativo não exista, vamos buscar e salvar os preços
            if not ativo_na_carteira:
                # Definir o período para baixar o histórico de preços
                mes_atual = simulacao.mes_atual
                data_inicio = mes_atual - timedelta(days=365)  # 1 ano antes do mês atual
                data_fim = mes_atual + timedelta(days=1)  # Inclui o mes_atual

                # Baixar o histórico de preços dos últimos 12 meses com preços não ajustados
                print(f"[DEBUG] Baixando histórico de preços de {data_inicio} até {data_fim} para {ticker}")
                historico_precos = yf.download(
                    ticker,
                    start=data_inicio.strftime('%Y-%m-%d'),
                    end=data_fim.strftime('%Y-%m-%d'),
                    auto_adjust=False,
                    actions=True
                )

                if historico_precos.empty:
                    print(f"[ERROR] Não foi possível obter o histórico de preços para o ativo {ticker}.")
                    return JsonResponse({'error': f'Não foi possível obter o histórico de preços para {ticker}.'}, status=404)

                # Salva o histórico de preços com todos os valores OHLC
                precos = {
                    str(index.date()): {
                        'open': float(row['Open']),
                        'high': float(row['High']),
                        'low': float(row['Low']),
                        'close': float(row['Close'])
                    }
                    for index, row in historico_precos.iterrows()
                }

                # Caso seja uma operação de compra
                if tipo_operacao == 'compra':
                    # Verifica se há dinheiro suficiente
                    if valor > carteira_manual.valor_em_dinheiro:
                        print("[ERROR] Saldo insuficiente.")
                        return JsonResponse({'error': 'Saldo insuficiente.'}, status=400)

                    # Atualiza o valor em dinheiro na carteira
                    carteira_manual.valor_em_dinheiro -= valor
                    print(f"[DEBUG] Novo valor em dinheiro na carteira: {carteira_manual.valor_em_dinheiro}")

                    # Calcula a quantidade comprada
                    quantidade_comprada = valor / preco_convertido
                    print(f"[DEBUG] Quantidade comprada: {quantidade_comprada}")

                    if ativo_na_carteira:
                        # Atualiza a posse do ativo existente na carteira
                        ativo_na_carteira.posse += quantidade_comprada
                        ativo_na_carteira.save()
                        print(f"[DEBUG] Nova posse do ativo existente: {ativo_na_carteira.posse}")
                    else:
                        # Se o ativo não está na carteira, cria um novo ativo e o adiciona à carteira
                        novo_ativo = Ativo.objects.create(
                            ticker=ticker,
                            nome=ticker,  # Aqui você pode ajustar para o nome real do ativo, se disponível
                            peso=0.0,  # Definir peso como 0 por enquanto ou outra lógica que faça sentido
                            posse=quantidade_comprada,
                            precos=precos,  # Armazena o histórico de preços com OHLC
                            data_lancamento=None  # Pode ajustar conforme necessário
                        )
                        carteira_manual.ativos.add(novo_ativo)
                        print(f"[DEBUG] Novo ativo criado e adicionado à carteira: {novo_ativo}")

                    # Salva as mudanças na carteira
                    carteira_manual.save()
                    print("[DEBUG] Carteira manual atualizada e salva.")

                    # Recarrega o ativo_na_carteira para obter a nova posse
                    ativo_na_carteira = carteira_manual.ativos.filter(ticker=ticker).first()
                    print(f"[DEBUG] Ativo recarregado: {ativo_na_carteira}")

                    return JsonResponse({
                        'novoDinheiroDisponivel': carteira_manual.valor_em_dinheiro,
                        'novaQuantidadeAtivo': ativo_na_carteira.posse,
                        'ticker': ticker
                    }, status=200)

                # Caso seja uma operação de venda
                elif tipo_operacao == 'venda':
                    if not ativo_na_carteira:
                        print("[ERROR] Ativo não encontrado na carteira.")
                        return JsonResponse({'error': 'Ativo não encontrado na carteira.'}, status=404)

                    # Calcula a quantidade de ativos a vender
                    quantidade_vendida = valor / preco_convertido
                    print(f"[DEBUG] Quantidade a ser vendida: {quantidade_vendida}")

                    # Verifica se o usuário tem ativos suficientes para vender
                    if quantidade_vendida > ativo_na_carteira.posse:
                        print("[ERROR] Quantidade insuficiente de ativos para vender.")
                        return JsonResponse({'error': 'Quantidade insuficiente de ativos para vender.'}, status=400)

                    # Atualiza a posse do ativo e o valor em dinheiro na carteira
                    ativo_na_carteira.posse -= quantidade_vendida
                    carteira_manual.valor_em_dinheiro += valor

                    ativo_na_carteira.save()
                    carteira_manual.save()

                    print(f"[DEBUG] Nova posse do ativo após venda: {ativo_na_carteira.posse}")
                    print(f"[DEBUG] Novo valor em dinheiro na carteira após venda: {carteira_manual.valor_em_dinheiro}")

                    return JsonResponse({
                        'novoDinheiroDisponivel': carteira_manual.valor_em_dinheiro,
                        'novaQuantidadeAtivo': ativo_na_carteira.posse,
                        'ticker': ticker
                    }, status=200)

                else:
                    print("[ERROR] Tipo de operação inválido.")
                    return JsonResponse({'error': 'Tipo de operação inválido.'}, status=400)

        except json.JSONDecodeError:
            print("[ERROR] Corpo da requisição inválido.")
            return JsonResponse({'error': 'Corpo da requisição inválido.'}, status=400)
        except Exception as e:
            print(f"[ERROR] Erro inesperado: {str(e)}")
            return JsonResponse({'error': f'Erro inesperado: {str(e)}'}, status=500)

    print("[ERROR] Método não permitido. Use POST.")
    return JsonResponse({'error': 'Método não permitido. Use POST.'}, status=405)
