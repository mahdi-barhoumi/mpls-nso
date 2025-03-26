import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from core.models import Site, Customer

@csrf_exempt
@require_http_methods(["GET"])
def list_customers(request):
    try:
        customers = Customer.objects.all()
        
        customer_list = []
        for customer in customers:
            customer_data = {
                'id': customer.id,
                'name': customer.name,
                'description': customer.description,
                'email': customer.email,
                'phone_number': customer.phone_number,
                'created_at': customer.created_at.isoformat(),
                'updated_at': customer.updated_at.isoformat()
            }
            customer_list.append(customer_data)
        
        return JsonResponse({
            'status': 'success',
            'data': customer_list
        })
    
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_customer(request, customer_id):
    try:
        customer = get_object_or_404(Customer, id=customer_id)
        
        customer_data = {
            'id': customer.id,
            'name': customer.name,
            'description': customer.description,
            'email': customer.email,
            'phone_number': customer.phone_number,
            'created_at': customer.created_at.isoformat(),
            'updated_at': customer.updated_at.isoformat(),
            'sites': [
                {
                    'id': site.id,
                    'name': site.name,
                    'location': site.location
                } for site in customer.sites.all()
            ]
        }
        
        return JsonResponse({
            'status': 'success',
            'data': customer_data
        })
    
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def create_customer(request):
    try:
        # Parse JSON data
        data = json.loads(request.body)
        
        # Validate required fields
        if 'name' not in data:
            return JsonResponse({
                'status': 'error',
                'message': 'Missing required field: name'
            }, status=400)
        
        # Create customer
        customer = Customer(
            name=data['name'],
            description=data.get('description', ''),
            email=data.get('email', ''),
            phone_number=data.get('phone_number', '')
        )
        
        # Validate customer
        try:
            customer.save()
        except ValidationError as e:
            return JsonResponse({
                'status': 'error',
                'message': e.message
            }, status=400)
        
        return JsonResponse({
            'status': 'success',
            'data': {
                'id': customer.id,
                'name': customer.name
            }
        }, status=201)
    
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON'
        }, status=400)
    
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
