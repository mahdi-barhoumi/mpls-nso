from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth.models import User

@method_decorator(csrf_exempt, name='dispatch')
class UserProfileView(View):
    def get(self, request):
        """Get current user profile"""
        # Get the first user as this is a local app
        user = User.objects.first()
        return JsonResponse({
            'username': user.username,
            'email': user.email
        })

    def put(self, request):
        """Update user settings"""
        try:
            import json
            data = json.loads(request.body)
            
            # Get the first user as this is a local app
            user = User.objects.first()
            
            # Update fields if provided
            if 'username' in data:
                user.username = data['username']
            if 'email' in data:
                user.email = data['email']
            if 'new_password' in data:
                user.set_password(data['new_password'])
            
            user.save()
            
            return JsonResponse({
                'message': 'Profile updated successfully',
                'user': {
                    'username': user.username,
                    'email': user.email
                }
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
