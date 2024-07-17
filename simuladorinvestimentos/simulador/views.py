from django.http import JsonResponse
from django.contrib.auth.decorators import login_required


@login_required
def home(request):
    data = {
        'message': 'Hello, World!',
        'status': 'success'
    }
    return JsonResponse({'data':data})
