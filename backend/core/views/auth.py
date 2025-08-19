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
            username = data.get('username', '').strip()
            password = data.get('password', '').strip()
            
            # Validate required fields
            if not username:
                return JsonResponse({
                    'error': 'Username is required',
                    'field': 'username'
                }, status=400)
                
            if not password:
                return JsonResponse({
                    'error': 'Password is required',
                    'field': 'password'
                }, status=400)
            
            # Attempt authentication
            user = authenticate(request, username=username, password=password)
            if user is not None:
                if not user.is_active:
                    return JsonResponse({
                        'error': 'Your account is disabled',
                        'field': 'username'
                    }, status=403)
                    
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
                    'error': 'Invalid username or password',
                    'field': 'password'
                }, status=401)
                
        except Exception as e:
            return JsonResponse({
                'error': 'An unexpected error occurred. Please try again later.',
                'detail': str(e)
            }, status=500)

    def delete(self, request):
        try:
            logout(request)
            return JsonResponse({
                'message': 'Logout successful'
            })
        except Exception as e:
            return JsonResponse({
                'error': 'Failed to log out. Please try again.',
                'detail': str(e)
            }, status=500)