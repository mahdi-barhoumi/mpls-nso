from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth import authenticate, login, logout

@method_decorator(csrf_exempt, name='dispatch')
class AuthView(View):
    def post(self, request):
        try:
            data = request.POST
            username = data.get('username')
            password = data.get('password')
            
            if not username or not password:
                return JsonResponse({
                    'error': 'Username and password are required'
                }, status=400)
            
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return JsonResponse({
                    'message': 'Login successful',
                    'user': {
                        'username': user.username,
                        'email': user.email,
                        'is_staff': user.is_staff,
                        'is_superuser': user.is_superuser
                    }
                })
            else:
                return JsonResponse({
                    'error': 'Invalid credentials'
                }, status=401)
                
        except Exception as e:
            return JsonResponse({
                'error': str(e)
            }, status=500)
    
    def delete(self, request):
        try:
            logout(request)
            return JsonResponse({
                'message': 'Logout successful'
            })
        except Exception as e:
            return JsonResponse({
                'error': str(e)
            }, status=500)