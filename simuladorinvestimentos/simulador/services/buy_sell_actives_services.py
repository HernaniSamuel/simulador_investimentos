import yfinance as yf
from datetime import timedelta
from django.shortcuts import get_object_or_404
from ..models import SimulacaoManual, Ativo


def processar_compra_venda(simulacao_id, user, tipo_operacao, valor, preco_convertido, ticker):
    try:
        # Obtém a simulação manual e a carteira associada
        simulacao = get_object_or_404(SimulacaoManual, id=simulacao_id, usuario=user)
        carteira_manual = simulacao.carteira_manual

        # Verifica se o ativo já existe na carteira dessa simulação
        ativo_na_carteira = carteira_manual.ativos.filter(ticker=ticker).first()

        # Caso o ativo não exista, busca o histórico de preços e salva
        if not ativo_na_carteira:
            # Define o período para baixar o histórico de preços
            mes_atual = simulacao.mes_atual
            data_inicio = mes_atual - timedelta(days=365)  # 1 ano antes do mês atual
            data_fim = mes_atual + timedelta(days=1)  # Inclui o mes_atual

            # Baixar o histórico de preços
            historico_precos = yf.download(
                ticker,
                start=data_inicio.strftime('%Y-%m-%d'),
                end=data_fim.strftime('%Y-%m-%d'),
                auto_adjust=False,
                actions=True
            )

            if historico_precos.empty:
                return {'error': f'Não foi possível obter o histórico de preços para {ticker}.'}, 404

            # Salva o histórico de preços
            precos = {
                str(index.date()): {
                    'open': float(row['Open']),
                    'high': float(row['High']),
                    'low': float(row['Low']),
                    'close': float(row['Close'])
                }
                for index, row in historico_precos.iterrows()
            }

        # Processa a compra de ativos
        if tipo_operacao == 'compra':
            if valor > carteira_manual.valor_em_dinheiro:
                return {'error': 'Saldo insuficiente.'}, 400

            carteira_manual.valor_em_dinheiro -= valor
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

        # Processa a venda de ativos
        elif tipo_operacao == 'venda':
            if not ativo_na_carteira:
                return {'error': 'Ativo não encontrado na carteira.'}, 404

            quantidade_vendida = valor / preco_convertido

            if quantidade_vendida > ativo_na_carteira.posse:
                return {'error': 'Quantidade insuficiente de ativos para vender.'}, 400

            ativo_na_carteira.posse -= quantidade_vendida
            carteira_manual.valor_em_dinheiro += valor

            ativo_na_carteira.save()
            carteira_manual.save()

            return {
                'novoDinheiroDisponivel': carteira_manual.valor_em_dinheiro,
                'novaQuantidadeAtivo': ativo_na_carteira.posse,
                'ticker': ticker
            }, 200

        else:
            return {'error': 'Tipo de operação inválido.'}, 400

    except Exception as e:
        return {'error': f'Erro inesperado: {str(e)}'}, 500
