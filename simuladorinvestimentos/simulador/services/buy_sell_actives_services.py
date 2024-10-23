from typing import Tuple, Dict, Union, Optional
import yfinance as yf
from datetime import timedelta
from django.shortcuts import get_object_or_404
from ..models import SimulacaoManual, Ativo
from ..utils import arredondar_para_baixo


def processar_compra_venda(
        simulacao_id: int,
        user: object,
        tipo_operacao: str,
        valor: float,
        preco_convertido: Optional[float],
        ticker: str
) -> Tuple[Dict[str, Union[str, float]], int]:
    """
    Process buy/sell operations for assets with improved error handling and validation.

    Args:
        simulacao_id: ID of the simulation
        user: User object
        tipo_operacao: Type of operation ('compra' or 'venda')
        valor: Amount to buy/sell
        preco_convertido: Converted price of the asset (None or 1 for BRL assets)
        ticker: Asset ticker symbol

    Returns:
        Tuple containing response dict and HTTP status code
    """
    try:
        # Input validation
        if not all([simulacao_id, user, tipo_operacao, valor, ticker]):
            print('\033[1;32mcampos obrigatórios\033[m')
            return {'error': 'Todos os campos são obrigatórios.'}, 400

        if tipo_operacao not in ['compra', 'venda']:
            return {'error': 'Tipo de operação inválido.'}, 400

        if valor <= 0:
            return {'error': 'Valor deve ser maior que zero.'}, 400

        # Se o preço convertido não for fornecido ou for None, assumimos que é um ativo em real
        preco_convertido = preco_convertido if preco_convertido is not None else 1.0

        if preco_convertido <= 0:
            return {'error': 'Preço convertido deve ser maior que zero.'}, 400

        # Get simulation and portfolio
        try:
            simulacao = get_object_or_404(SimulacaoManual, id=simulacao_id, usuario=user)
            carteira_manual = simulacao.carteira_manual
        except Exception:
            return {'error': 'Simulação não encontrada.'}, 404

        # Get or create asset in portfolio
        ativo_na_carteira = carteira_manual.ativos.filter(ticker=ticker).first()

        # Handle new asset creation
        if not ativo_na_carteira:
            mes_atual = simulacao.mes_atual
            data_inicio = mes_atual - timedelta(days=365)
            data_fim = mes_atual + timedelta(days=1)

            try:
                historico_precos = yf.download(
                    ticker,
                    start=data_inicio.strftime('%Y-%m-%d'),
                    end=data_fim.strftime('%Y-%m-%d'),
                    auto_adjust=False,
                    actions=True
                )

                if historico_precos.empty:
                    return {'error': f'Histórico de preços não disponível para {ticker}.'}, 404

                precos = {
                    str(index.date()): {
                        'open': float(row['Open']),
                        'high': float(row['High']),
                        'low': float(row['Low']),
                        'close': float(row['Close'])
                    }
                    for index, row in historico_precos.iterrows()
                }
            except Exception as e:
                return {'error': f'Erro ao obter dados do ativo {ticker}: {str(e)}'}, 400

        # Process purchase
        if tipo_operacao == 'compra':
            valor = arredondar_para_baixo(valor)
            if valor > carteira_manual.valor_em_dinheiro:
                return {
                    'error': 'Saldo insuficiente.',
                    'saldo_atual': carteira_manual.valor_em_dinheiro,
                    'valor_necessario': valor
                }, 400

            try:
                carteira_manual.valor_em_dinheiro -= valor
                carteira_manual.valor_em_dinheiro = arredondar_para_baixo(carteira_manual.valor_em_dinheiro)
                quantidade_comprada = valor / preco_convertido

                if ativo_na_carteira:
                    ativo_na_carteira.posse += quantidade_comprada
                    ativo_na_carteira.save()
                else:
                    novo_ativo = Ativo.objects.create(
                        ticker=ticker,
                        nome=ticker,
                        peso=0.0,
                        posse=quantidade_comprada,
                        precos=precos,
                        ultimo_preco_convertido=preco_convertido,
                        data_lancamento=None
                    )
                    carteira_manual.ativos.add(novo_ativo)

                carteira_manual.save()
                ativo_na_carteira = carteira_manual.ativos.filter(ticker=ticker).first()

                return {
                    'novoDinheiroDisponivel': carteira_manual.valor_em_dinheiro,
                    'novaQuantidadeAtivo': ativo_na_carteira.posse,
                    'ticker': ticker
                }, 200
            except Exception as e:
                return {'error': f'Erro ao processar compra: {str(e)}'}, 500

        # Process sale
        elif tipo_operacao == 'venda':
            if not ativo_na_carteira:
                return {'error': 'Ativo não encontrado na carteira.'}, 404

            # Converter valor monetário para quantidade de ações
            quantidade_vendida = valor / preco_convertido

            if quantidade_vendida > ativo_na_carteira.posse:
                print(f'\033[1;32mQuantidade a vender: {quantidade_vendida}, Posse atual: {ativo_na_carteira.posse}\033[m')
                return {
                    'error': 'Quantidade insuficiente de ativos para vender.',
                    'quantidade_disponivel': ativo_na_carteira.posse,
                    'quantidade_solicitada': quantidade_vendida
                }, 400

            try:
                ativo_na_carteira.posse -= quantidade_vendida
                carteira_manual.valor_em_dinheiro += valor  # Usa o valor monetário original

                ativo_na_carteira.save()
                carteira_manual.save()

                return {
                    'novoDinheiroDisponivel': carteira_manual.valor_em_dinheiro,
                    'novaQuantidadeAtivo': ativo_na_carteira.posse,
                    'ticker': ticker
                }, 200
            except Exception as e:
                return {'error': f'Erro ao processar venda: {str(e)}'}, 500

    except Exception as e:
        return {'error': f'Erro inesperado: {str(e)}'}, 500
