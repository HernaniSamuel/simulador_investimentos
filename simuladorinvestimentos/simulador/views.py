from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
import yfinance as yf
import json


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
