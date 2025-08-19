import json
from django.views import View
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.db import IntegrityError
from core.models import Customer

@method_decorator(csrf_exempt, name='dispatch')
class CustomerView(View):
    def get(self, request, customer_id=None):
        try:
            if customer_id:
                # Get specific customer
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
                            'location': site.location,
                            'description': site.description,
                            'link_network': site.link_network,
                            'router': site.router.hostname if site.router else None,
                            'vrf': site.vrf.name if site.vrf else None,
                        } for site in customer.sites.all()
                    ],
                    'vpns': [
                        {
                            'id': vpn.id,
                            'name': vpn.name,
                            'description': vpn.description,
                            'sites': [
                                {'id': s.id, 'name': s.name}
                                for s in vpn.sites.all()
                            ]
                        } for vpn in customer.vpns.all()
                    ]
                }
                return JsonResponse(customer_data)
            else:
                # List all customers
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
                
                return JsonResponse(customer_list, safe=False)
        
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    def post(self, request):
        try:
            # Parse JSON data
            data = json.loads(request.body)
            
            # Validate required fields
            if 'name' not in data:
                return JsonResponse({'error': 'Missing required field: name'}, status=400)
            
            # Check for existing customer with the same name
            existing_customer = Customer.objects.filter(name__iexact=data['name']).exists()
            if existing_customer:
                return JsonResponse({'error': f"Customer with name '{data['name']}' already exists"}, status=409)
            
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
            except (ValidationError, IntegrityError) as e:
                return JsonResponse({'error': str(e)}, status=400)
            
            return JsonResponse({
                'id': customer.id,
                'name': customer.name
            }, status=201)
        
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    def put(self, request, customer_id):
        try:
            # Get the customer
            customer = get_object_or_404(Customer, id=customer_id)
            
            # Parse JSON data
            data = json.loads(request.body)
            
            # Check if name is being updated
            if 'name' in data:
                # Check for existing customer with the new name (excluding current customer)
                existing_customer = Customer.objects.filter(
                    name__iexact=data['name']
                ).exclude(id=customer_id).exists()
                
                if existing_customer:
                    return JsonResponse({'error': f"Customer with name '{data['name']}' already exists"}, status=409)
                
                customer.name = data['name']
            
            # Update other fields
            if 'description' in data:
                customer.description = data['description']
            if 'email' in data:
                customer.email = data['email']
            if 'phone_number' in data:
                customer.phone_number = data['phone_number']
            
            # Validate and save
            try:
                customer.save()
            except (ValidationError, IntegrityError) as e:
                return JsonResponse({'error': str(e)}, status=400)
            
            return JsonResponse({
                'id': customer.id,
                'name': customer.name,
                'description': customer.description,
                'email': customer.email,
                'phone_number': customer.phone_number
            })
        
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    def delete(self, request, customer_id):
        try:
            # Get the customer
            customer = get_object_or_404(Customer, id=customer_id)
            
            # Store details before deletion
            customer_name = customer.name
            
            # Delete the customer
            customer.delete()
            
            return JsonResponse({
                'message': f'Customer {customer_name} deleted successfully'
            }, status=204)
        
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
