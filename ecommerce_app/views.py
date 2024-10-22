from django.shortcuts import render,redirect,get_object_or_404
from .form import CustomUserForm
from . models import *
from django.contrib import messages
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
import json
import logging
from django.db import transaction
from django.http import HttpResponseBadRequest


def home(request):
    products=Product.objects.filter(trending=1)
    return render(request,"ecommerce/home.html",{"products":products})

def login_page(request):
    if request.user.is_authenticated:
        return redirect("/")  # Already logged in, redirect to home

    if request.method == 'POST':
        name = request.POST.get('username')
        pwd = request.POST.get('password')
        user = authenticate(request, username=name, password=pwd)

        if user is not None:
            login(request, user)
            messages.success(request, "Logged in Successfully")

            # Check if the user is an admin or regular user
            if user.is_staff:  # Admin users
                print('hello from admin')
                return redirect('admin_dashboard')  # Redirect to admin dashboard
            else:  # Regular users
                return redirect('/')  # Redirect to home or user dashboard
        else:
            messages.error(request, "Invalid User Name or Password")
            return redirect("/login")

    return render(request, "ecommerce/login.html")
 
def register(request):
  form=CustomUserForm()
  if request.method=='POST':
    form=CustomUserForm(request.POST)
    if form.is_valid():
      form.save()
      messages.success(request,"Registration Success You can Login Now..!")
      return redirect('/login')
  return render(request,"ecommerce/register.html",{'form':form})

def logout_page(request):
      if request.user.is_authenticated:
          logout(request)
          messages.success(request,"Logged out Successfully")
          return redirect("/")
       
def collections(request):
    catagory=Category.objects.filter(status=0)
    return render(request,"ecommerce/collection.html",{"catagory":catagory})
 
def collections_view(request,name):
  if(Category.objects.filter(name=name,status=0)):
      products=Product.objects.filter(category__name=name)
      return render(request,"ecommerce/products/index.html",{"products":products,"category_name":name})
  else:
        return redirect('collections')
    

def product_details(request,category, product):
    category = get_object_or_404(Category, name__iexact=category,status=0)
    product = get_object_or_404(Product, name__iexact=product, category=category,status=0)

    if product:
        return render(request, 'ecommerce/products/product_detail.html', {'product': product, 'category': category})
    else:
        messages.error(request, "No Such Product Found")
        return redirect('collections')
    
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    quantity = int(request.POST.get('quantity', 1))
    
    if request.user.is_authenticated:
        cart_item, created = Cart.objects.get_or_create(
            user=request.user,
            product=product,
            defaults={'product_qty': quantity}
        )
    else:
        session_id = request.session.session_key
        if not session_id:
            request.session.create()
            session_id = request.session.session_key
        cart_item, created = Cart.objects.get_or_create(
            session_id=session_id,
            product=product,
            defaults={'product_qty': quantity}
        )
    
    if not created:
        cart_item.product_qty += quantity
        cart_item.save()
    
    messages.success(request, f"{quantity} {product.name}(s) added to cart.")
    return redirect('cart')
 
def cart_page(request):
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user)
    else:
        session_id = request.session.session_key
        if not session_id:
            request.session.create()  
            session_id = request.session.session_key

        cart = Cart.objects.filter(session_id=session_id)

    if cart.exists():
        return render(request, "ecommerce/cart/cart.html", {"cart": cart})
    else:
        return render(request, "ecommerce/cart/cart.html", {"cart": []})

 
def remove_cart(request,cid):
    cartitem=Cart.objects.get(id=cid)
    cartitem.delete()
    return redirect("/cart")



def update_cart(request, product_id):
    action = request.POST.get('action')
    
    if request.user.is_authenticated:
        # Authenticated user - Get the cart item for the logged-in user
        cart_item = get_object_or_404(Cart, product_id=product_id, user=request.user)
    else:
        # Unauthenticated user - Get the session ID and find the cart item
        session_id = request.session.session_key
        if not session_id:
            request.session.create()  # Create a new session if it doesn't exist
            session_id = request.session.session_key

        cart_item = get_object_or_404(Cart, product_id=product_id, session_id=session_id)

    # Handle the action (increase or decrease quantity)
    if action == 'increase':
        cart_item.product_qty += 1
    elif action == 'decrease' and cart_item.product_qty > 1:
        cart_item.product_qty -= 1
    else:
        # Optionally, if the quantity is 0 or the action is to remove, delete the cart item
        cart_item.delete()
        return redirect('cart')

    # Save the updated cart item
    cart_item.save()
    
    return redirect('cart')


@login_required
def create_order(request, category_id, product_id):
    product = get_object_or_404(Product, id=product_id)
    category = get_object_or_404(Category, id=category_id)
    addresses = request.user.addresses.all()
    total_quantity = 0
    total_amount = 0

    if request.method == 'POST':
        quantity = request.POST.get('quantity')
        selected_address_id = request.POST.get('shipping_address')
        
        new_address_data = {
            'name': request.POST.get('new_address_name'),
            'street': request.POST.get('new_address_street'),
            'city': request.POST.get('new_address_city'),
            'state': request.POST.get('new_address_state'),
            'zip_code': request.POST.get('new_address_zip_code'),
        }

        if not quantity:
            messages.error(request, "Quantity is required")
            return render(request, 'ecommerce/order/create_order.html', {'products': [product], 'category': category, 'addresses': addresses})

        try:
            quantity = int(quantity)
        except ValueError:
            messages.error(request, "Invalid quantity")
            return render(request, 'ecommerce/order/create_order.html', {'products': [product], 'category': category, 'addresses': addresses})

        total_quantity = quantity
        total_amount = product.selling_price * total_quantity

        if selected_address_id:
            shipping_address = get_object_or_404(Address, id=selected_address_id, user=request.user)
        elif all(new_address_data.values()):
            shipping_address = Address.objects.create(user=request.user, **new_address_data)
        else:
            messages.error(request, "Please select an existing address or enter a new one")
            return render(request, 'ecommerce/order/create_order.html', {
                'products': [product], 
                'category': category, 
                'addresses': addresses,
                'total_quantity': total_quantity,
                'total_amount': total_amount
            })

        if product.quantity < quantity:
            messages.error(request, "Not enough stock available")
            return render(request, 'ecommerce/order/create_order.html', {
                'products': [product], 
                'category': category, 
                'addresses': addresses,
                'total_quantity': total_quantity,
                'total_amount': total_amount
            })

        total_price = product.selling_price * quantity

        try:
            with transaction.atomic():
                order = Order.objects.create(
                    user=request.user,
                    shipping_address=f"{shipping_address.name}, {shipping_address.street}, {shipping_address.city}, {shipping_address.state}, {shipping_address.zip_code}",
                    total_price=total_price,
                    is_paid=False,
                    status='pending'
                )

                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    unit_price=product.selling_price
                )

                product.quantity -= quantity
                product.save()

            return redirect('payment', order_id=order.id)
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return render(request, 'ecommerce/order/create_order.html', {
                'products': [product], 
                'category': category, 
                'addresses': addresses,
                'total_quantity': total_quantity,
                'total_amount': total_amount
            })

    return render(request, 'ecommerce/order/create_order.html', {
        'products': [product], 
        'category': category,  
        'addresses': addresses,
        'total_quantity': total_quantity,
        'total_amount': total_amount
    })

@login_required
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if order.status in ['pending', 'processing']:
        order.status = 'canceled'
        # Logic to increase the stock of the products in the order
        for item in order.orderitem_set.all():
            item.product.quantity += item.quantity  # Assuming you have an order item model
            item.product.save()
        order.save()    
        messages.success(request, "Order canceled successfully.")
    else:
        messages.error(request, "Cannot cancel this order.")
        return redirect('order_list_user')
    return render(request, 'ecommerce/order/cancel_order.html', {'order': order})



@login_required
def order_list_user(request):
    orders = Order.objects.filter(user=request.user).order_by('-order_date')
    context = {
        'orders': orders
    }
    return render(request, 'ecommerce/order/order_list_user.html', context)

@login_required
def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk)
    order_items = OrderItem.objects.filter(order=order)
    context = {
        'order': order,
        'order_items': order_items,
    }
    return render(request, 'ecommerce/order/order_detail.html', context)


def product_list(request,):
    products = Product.objects.filter(status=False)     
    category_ids = request.GET.getlist('category')  
    min_price = request.GET.get('min_price')       
    max_price = request.GET.get('max_price')       
    trending = request.GET.get('trending')         

    if category_ids:
        products = products.filter(category__id__in=category_ids)
    
    if min_price:
        products = products.filter(selling_price__gte=min_price)
    
    if max_price:
        products = products.filter(selling_price__lte=max_price)
    
    if trending:
        products = products.filter(trending=True)

    # Sorting logic
    sort_by = request.GET.get('sort')
    if sort_by == 'price_asc':
        products = products.order_by('selling_price')
    elif sort_by == 'price_desc':
        products = products.order_by('-selling_price')

    context = {
        'products': products,
        'categories': Category.objects.all(),
        'selected_categories': category_ids,  
    }

    return render(request, 'ecommerce/products/filter.html', context)



logger = logging.getLogger(__name__)
@login_required
def payment(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    if request.method == 'POST':
        # Get payment details from the form
        payment_method = request.POST.get('payment_method')
        amount = request.POST.get('amount')  # Amount should match the order total  

        # Validate payment details
        if not payment_method or not amount:
            messages.error(request, "Invalid payment details. All fields are required.")
            return render(request, 'ecommerce/payment/payment.html', {'order': order})

        try:
            # Ensure the payment amount matches the order total
            if float(amount) != order.total_price:
                messages.error(request, "Payment amount does not match the order total.")
                return render(request, 'ecommerce/payment/payment.html', {'order': order})

            # Simulate payment processing and create a Payment record
            payment = Payment.objects.create(
                order=order,
                amount=amount,
                payment_method=payment_method,
                payment_status=False,  # Assuming payment is successful  
            )
            
            # Update the order status to paid
            order.is_paid = False
            order.save()

            # Display success message and redirect
            messages.success(request, "successful! Your order is confirmed.")
            return redirect('payment_success')
        
        except Exception as e:
            logger.error(f"Payment processing failed: {str(e)}")
            messages.error(request, "Payment processing error. Please try again.")
            return render(request, 'ecommerce/payment/payment.html', {'order': order})
    
    return render(request, 'ecommerce/payment/payment.html', {'order': order})

@login_required
def payment_detail(request, pk):
    order = get_object_or_404(Order, pk=pk)
    payment = Payment.objects.filter(order=order).first()
    if not payment:
        return render(request, 'ecommerce/order/no_payment_found.html', {'order': order})

    return render(request, 'ecommerce/order/payment_detail.html', {'order': order, 'payment': payment})

@login_required
def payment_success(request):
    return render(request, 'ecommerce/payment/payment_success.html')


#----AdminViews
def admin_check(user):
    return user.is_staff

@login_required
@user_passes_test(admin_check)
def admin_dashboard(request):
    return render(request, 'ecommerce/admin_layouts/dashboard.html')


@login_required
@user_passes_test(admin_check)
def create_catagory(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        status = request.POST.get('status') == '1'  # Converts to boolean
        image = request.FILES.get('image')

        # Create and save the Catagory object
        Category.objects.create(
            name=name,
            description=description,
            status=status,
            image=image
        )
        return redirect('list_catagory')
    
    return render(request, 'ecommerce/admin_layouts/create_category.html')

# Read/List View
@login_required
@user_passes_test(admin_check)
def list_catagory(request):
    catagories = Category.objects.all()
    return render(request, 'ecommerce/admin_layouts/catagory_list.html', {'catagories': catagories})

# Update View
@login_required
@user_passes_test(admin_check)
def update_catagory(request, id):
    catagory = get_object_or_404(Category, id=id)
    
    if request.method == 'POST':
        catagory.name = request.POST.get('name')
        catagory.description = request.POST.get('description')
        catagory.status = request.POST.get('status') == '1'
        if request.FILES.get('image'):
            catagory.image = request.FILES.get('image')
        
        catagory.save()
        return redirect('list_catagory')
    
    return render(request, 'ecommerce/admin_layouts/update_catagory.html', {'catagory': catagory})

@login_required
@user_passes_test(admin_check)
@require_http_methods(["POST"])
def delete_catagory(request, id):
    catagory = get_object_or_404(Category, id=id)
    catagory.delete()
    return redirect('list_catagory')

# Create Product
@login_required
@user_passes_test(admin_check)
def create_product(request):
    categories = Category.objects.all()  # For category dropdown
    if request.method == 'POST':
        category_id = request.POST.get('category')
        name = request.POST.get('name')
        vendor = request.POST.get('vendor')
        product_image = request.FILES.get('product_image')
        quantity = request.POST.get('quantity')
        original_price = request.POST.get('original_price')
        selling_price = request.POST.get('selling_price')
        description = request.POST.get('description')
        status = request.POST.get('status') == '1'
        trending = request.POST.get('trending') == '1'

        category = Category.objects.get(id=category_id)

        # Create and save the Product object
        Product.objects.create(
            category=category,
            name=name,
            vendor=vendor,
            product_image=product_image,
            quantity=quantity,
            original_price=original_price,
            selling_price=selling_price,
            description=description,
            status=status,
            trending=trending
        )
        return redirect('list_products')
    
    return render(request, 'ecommerce/admin_layouts/add_product.html', {'categories': categories})

# List Products
@login_required
@user_passes_test(admin_check)
def list_products(request):
    products = Product.objects.all()
    return render(request, 'ecommerce/admin_layouts/product_list.html', {'products': products})

# Update Product
@login_required
@user_passes_test(admin_check)
def update_product(request, id):
    product = get_object_or_404(Product, id=id)
    categories = Category.objects.all()

    if request.method == 'POST':
        product.category_id = request.POST.get('category')
        product.name = request.POST.get('name')
        product.vendor = request.POST.get('vendor')
        product.quantity = request.POST.get('quantity')
        product.original_price = request.POST.get('original_price')
        product.selling_price = request.POST.get('selling_price')
        product.description = request.POST.get('description')
        product.status = request.POST.get('status') == '1'
        product.trending = request.POST.get('trending') == '1'

        if request.FILES.get('product_image'):
            product.product_image = request.FILES.get('product_image')

        product.save()
        return redirect('list_products')

    return render(request, 'ecommerce/admin_layouts/update_product.html', {'product': product, 'categories': categories})

# Delete Product
@login_required
@user_passes_test(admin_check)
@require_http_methods(["POST"])
def delete_product(request, id):
    product = get_object_or_404(Product, id=id)
    product.delete()
    return redirect('list_products')

@login_required
@user_passes_test(admin_check)
def users_list(request):
    users = User.objects.all()
    paginator = Paginator(users, 10)  # Show 10 users per page.
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'ecommerce/admin_layouts/users_list.html', {'page_obj': page_obj})

@login_required
@user_passes_test(admin_check)
def admin_cart_page(request):
    if request.user.is_authenticated:
        # Fetch cart items for the authenticated user
        cart = Cart.objects.filter(user=request.user)
    else:
        # Fetch cart items for the guest user based on session ID
        session_id = request.session.session_key
        if not session_id:
            request.session.create()  # Create session if it doesn't exist
            session_id = request.session.session_key

        cart = Cart.objects.filter(session_id=session_id)

    if cart.exists():
        return render(request, "ecommerce/admin_layouts/cart.html", {"cart": cart})
    else:
        return render(request, "ecommerce/admin_layouts/cart.html", {"cart": []})

@login_required
@user_passes_test(admin_check)
def admin_order_list(request):
    if not request.user.is_staff:
        return redirect('index')  # Redirect if the user is not an admin
    
    orders = Order.objects.all().order_by('id')  # Get all orders ordered by latest
    context = {
        'orders': orders,
    }
    return render(request, 'ecommerce/admin_layouts/admin_order_list.html', context)

@login_required
@user_passes_test(admin_check)
def admin_order_detail(request, order_id):
    if not request.user.is_staff:
        return redirect('index')  # Redirect if the user is not an admin

    order = get_object_or_404(Order, id=order_id)
    context = {
        'order': order,
    }
    return render(request, 'ecommerce/admin_layouts/admin_order_detail.html', context)

@login_required
@user_passes_test(admin_check)
def admin_cart_list(request):
    if not request.user.is_staff:
        return redirect('index')  # Redirect if the user is not an admin
    
    cart_items = Cart.objects.all().order_by('id')  # Get all cart items
    context = {
        'cart_items': cart_items,
    }
    return render(request, 'ecommerce/admin_layouts/admin_cart_list.html', context)

@login_required
@user_passes_test(admin_check)
def admin_payment_list(request):
    payments = Payment.objects.all()
    return render(request, 'ecommerce/admin_layouts/payment_list.html', {'payments': payments})

def profile_view(request):
    user = request.user
    addresses = Address.objects.filter(user=user)
    return render(request, 'ecommerce/profile/profile_page.html', {'user': user, 'addresses': addresses})

@login_required
def profile_view(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    addresses = Address.objects.filter(user=request.user)

    if request.method == 'POST':
        if 'profile_image' in request.FILES:
            profile.profile_image = request.FILES['profile_image']
            profile.save()
        return redirect('profile')

    return render(request, 'ecommerce/profile/profile_page.html', {'profile': profile, 'addresses': addresses})

@login_required
def add_address(request):
    if request.method == 'POST':
        Address.objects.create(
            user=request.user,
            name=request.POST['name'],
            street=request.POST['street'],
            city=request.POST['city'],
            state=request.POST['state'],
            zip_code=request.POST['zip_code']
        )
        return redirect('profile')
    return render(request, 'ecommerce/profile/add_address.html')

@login_required
def delete_address(request, address_id):
    address = Address.objects.get(id=address_id, user=request.user)
    if address:
        address.delete()
    return redirect('profile')

@login_required
def edit_address(request, address_id):
    address = Address.objects.get(id=address_id, user=request.user)
    if request.method == 'POST':
        address.name = request.POST['name']
        address.street = request.POST['street']
        address.city = request.POST['city']
        address.state = request.POST['state']
        address.zip_code = request.POST['zip_code']
        address.save()
        return redirect('profile')
    return render(request, 'ecommerce/profile/edit_address.html', {'address': address})


@login_required
def create_order_from_cart(request):
    cart_items = Cart.objects.filter(user=request.user)
    addresses = request.user.addresses.all()
    total_quantity = sum(item.product_qty for item in cart_items)
    total_amount = sum(item.total_cost for item in cart_items)

    if request.method == 'POST':
        selected_address_id = request.POST.get('shipping_address')
        new_address_data = {
            'name': request.POST.get('new_address_name'),
            'street': request.POST.get('new_address_street'),
            'city': request.POST.get('new_address_city'),
            'state': request.POST.get('new_address_state'),
            'zip_code': request.POST.get('new_address_zip_code'),
        }

        # Validate selected address or new address
        if selected_address_id:
            shipping_address = get_object_or_404(Address, id=selected_address_id, user=request.user)
        elif all(new_address_data.values()):
            shipping_address = Address.objects.create(user=request.user, **new_address_data)
        else:
            messages.error(request, "Please select an existing address or enter a new one.")
            return render(request, 'ecommerce/order/create_order_from_cart.html', {
                'cart_items': cart_items,
                'addresses': addresses,
                'total_quantity': total_quantity,
                'total_amount': total_amount
            })

        # Check stock availability and create order
        total_price = 0
        for item in cart_items:
            if item.product.quantity < item.product_qty:
                messages.error(request, f"Not enough stock available for {item.product.name}.")
                return render(request, 'ecommerce/order/create_order_from_cart.html', {
                    'cart_items': cart_items,
                    'addresses': addresses,
                    'total_quantity': total_quantity,
                    'total_amount': total_amount
                })
            total_price += item.total_cost

        try:
            with transaction.atomic():
                order = Order.objects.create(
                    user=request.user,
                    shipping_address=f"{shipping_address.name}, {shipping_address.street}, {shipping_address.city}, {shipping_address.state}, {shipping_address.zip_code}",
                    total_price=total_price,
                    is_paid=False,
                    status='pending'
                )

                for item in cart_items:
                    OrderItem.objects.create(
                        order=order,
                        product=item.product,
                        quantity=item.product_qty,
                        unit_price=item.product.selling_price
                    )
                    # Reduce product stock
                    item.product.quantity -= item.product_qty
                    item.product.save()

                # Clear the cart after creating the order
                cart_items.delete()

            return redirect('payment', order_id=order.id)
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return render(request, 'ecommerce/order/create_order_from_cart.html', {
                'cart_items': cart_items,
                'addresses': addresses,
                'total_quantity': total_quantity,
                'total_amount': total_amount
            })

    return render(request, 'ecommerce/order/create_order_from_cart.html', {
        'cart_items': cart_items,
        'addresses': addresses,
        'total_quantity': total_quantity,
        'total_amount': total_amount
    })