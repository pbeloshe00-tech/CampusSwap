
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login as auth_login, logout
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import (
    UserCreationForm,
    AuthenticationForm,
    PasswordChangeForm
)
from django.db import transaction
from django.db import models
from django.db.models import Count, Avg
from django.http import JsonResponse

from .forms import (
    ProductForm,
    ProfileForm,
    ExchangeRequestForm,
    SellerReviewForm
)

from .models import (
    Product,
    ExchangeRequest,
    Notification,
    Conversation,
    ChatMessage,
    Wishlist,
    RecentlyViewed,
    SellerReview
)


# HOME PAGE
def home(request):
    query = request.GET.get('q', '').strip()
    category = request.GET.get('category', '').strip()

    products = Product.objects.all().order_by('-created_at')

    if query:
        products = products.filter(name__icontains=query)

    if category:
        products = products.filter(category__iexact=category)

    # TRENDING PRODUCTS
    trending_products = Product.objects.filter(
        status='Available'
    ).annotate(
        wishlist_count=Count('wishlisted_by')
    ).filter(
        wishlist_count__gt=0
    ).order_by(
        '-wishlist_count',
        '-created_at'
    )[:4]

    # STUDENT DEALS
    student_deals = Product.objects.filter(
        status='Available',
        price__lte=500
    ).select_related(
        'seller'
    ).order_by(
        'price',
        '-created_at'
    )[:4]

    wishlist_product_ids = []
    recently_viewed_products = []

    if request.user.is_authenticated:

        wishlist_product_ids = Wishlist.objects.filter(
            user=request.user
        ).values_list('product_id', flat=True)

        recently_viewed_products = RecentlyViewed.objects.filter(
            user=request.user
        ).select_related(
            'product',
            'product__seller'
        ).exclude(
            product__status='Sold'
        )[:4]

    context = {
        'products': products,
        'query': query,
        'selected_category': category,
        'categories': Product.CATEGORY_CHOICES,
        'wishlist_product_ids': wishlist_product_ids,
        'trending_products': trending_products,
        'recently_viewed_products': recently_viewed_products,
        'student_deals': student_deals,
    }

    return render(request, 'marketplace/home.html', context)


# STUDENT REGISTRATION
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)

        if form.is_valid():
            user = form.save()
            auth_login(request, user)

            messages.success(
                request,
                'Registration successful! Welcome to Campus Swap.'
            )

            return redirect('home')
    else:
        form = UserCreationForm()

    return render(
        request,
        'marketplace/register.html',
        {'form': form}
    )


# STUDENT LOGIN
def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)

        if form.is_valid():
            auth_login(request, form.get_user())

            messages.success(
                request,
                'Login successful! Welcome back.'
            )

            return redirect('home')
    else:
        form = AuthenticationForm()

    return render(
        request,
        'marketplace/login.html',
        {'form': form}
    )


# ADD PRODUCT
@login_required
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)

        if form.is_valid():
            product = form.save(commit=False)
            product.seller = request.user
            product.save()

            messages.success(
                request,
                'Your product has been added successfully!'
            )

            return redirect('home')
    else:
        form = ProductForm()

    return render(
        request,
        'marketplace/add_product.html',
        {'form': form}
    )


# PRODUCT DETAILS
def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    existing_exchange_request = None
    is_in_wishlist = False
    has_reviewed = False

    if request.user.is_authenticated:

        # SAVE OR UPDATE RECENTLY VIEWED PRODUCT
        RecentlyViewed.objects.update_or_create(
            user=request.user,
            product=product,
            defaults={}
        )

        existing_exchange_request = ExchangeRequest.objects.filter(
            product=product,
            requester=request.user
        ).first()

        is_in_wishlist = Wishlist.objects.filter(
            user=request.user,
            product=product
        ).exists()

        if existing_exchange_request:
            has_reviewed = SellerReview.objects.filter(
                exchange_request=existing_exchange_request
            ).exists()

    # SELLER REVIEWS
    seller_reviews = SellerReview.objects.filter(
        seller=product.seller
    ).select_related(
        'reviewer'
    )

    seller_average_rating = seller_reviews.aggregate(
        average=Avg('rating')
    )['average']

    context = {
        'product': product,
        'exchange_form': ExchangeRequestForm(),
        'existing_exchange_request': existing_exchange_request,
        'is_in_wishlist': is_in_wishlist,
        'seller_reviews': seller_reviews,
        'seller_average_rating': seller_average_rating,
        'seller_review_count': seller_reviews.count(),
        'has_reviewed': has_reviewed,
    }

    return render(
        request,
        'marketplace/product_detail.html',
        context
    )


# SEND EXCHANGE REQUEST
@login_required
def send_exchange_request(request, product_id):
    if request.method != 'POST':
        return redirect('product_detail', product_id=product_id)

    product = get_object_or_404(Product, id=product_id)

    if product.seller == request.user:
        messages.error(
            request,
            'You cannot request an exchange for your own product!'
        )
        return redirect('product_detail', product_id=product.id)

    if product.status != 'Available':
        messages.error(
            request,
            'Sorry, this product is no longer available!'
        )
        return redirect('product_detail', product_id=product.id)

    existing_request = ExchangeRequest.objects.filter(
        product=product,
        requester=request.user
    ).first()

    if existing_request:
        messages.warning(
            request,
            'You have already sent an exchange request for this product.'
        )
        return redirect('product_detail', product_id=product.id)

    form = ExchangeRequestForm(request.POST)

    if form.is_valid():
        exchange_request = form.save(commit=False)
        exchange_request.product = product
        exchange_request.requester = request.user
        exchange_request.save()

        Notification.objects.create(
            recipient=product.seller,
            message=(
                f"{request.user.username} sent an exchange request "
                f"for {product.name}."
            ),
            exchange_request=exchange_request
        )

        messages.success(
            request,
            'Your exchange request has been sent successfully!'
        )
    else:
        messages.error(
            request,
            'Please check your exchange request message.'
        )

    return redirect('product_detail', product_id=product.id)


# STUDENT DASHBOARD
@login_required
def dashboard(request):

    my_products = Product.objects.filter(
        seller=request.user
    ).order_by('-created_at')

    received_requests = ExchangeRequest.objects.filter(
        product__seller=request.user
    ).select_related(
        'product', 'requester'
    ).order_by('-created_at')

    sent_requests = ExchangeRequest.objects.filter(
        requester=request.user
    ).select_related(
        'product', 'product__seller'
    ).order_by('-created_at')

    notifications = Notification.objects.filter(
        recipient=request.user
    ).order_by('-created_at')

    unread_notifications_count = notifications.filter(
        is_read=False
    ).count()

    context = {
        'my_products': my_products,
        'received_requests': received_requests,
        'sent_requests': sent_requests,
        'notifications': notifications,
        'unread_notifications_count': unread_notifications_count,
    }

    return render(
        request,
        'marketplace/dashboard.html',
        context
    )


# MARK NOTIFICATION AS READ
@login_required
def mark_notification_read(request, notification_id):

    if request.method == 'POST':

        notification = get_object_or_404(
            Notification,
            id=notification_id,
            recipient=request.user
        )

        notification.is_read = True
        notification.save()

        messages.success(
            request,
            'Notification marked as read.'
        )

    return redirect('dashboard')


# ACCEPT EXCHANGE REQUEST
@login_required
def accept_exchange_request(request, request_id):
    if request.method != 'POST':
        return redirect('dashboard')

    with transaction.atomic():
        exchange = get_object_or_404(
            ExchangeRequest.objects.select_for_update().select_related('product'),
            id=request_id,
            product__seller=request.user
        )

        product = Product.objects.select_for_update().get(
            id=exchange.product_id
        )

        if exchange.status != 'Pending':
            messages.warning(
                request,
                'This exchange request has already been processed.'
            )
            return redirect('dashboard')

        if product.status != 'Available':
            messages.error(
                request,
                'This product is no longer available.'
            )
            return redirect('dashboard')

        exchange.status = 'Accepted'
        exchange.save()

        Notification.objects.create(
            recipient=exchange.requester,
            message=(
                f"Your exchange request for {product.name} "
                f"has been accepted!"
            ),
            exchange_request=exchange
        )

        product.status = 'Sold'
        product.save()

        other_requests = ExchangeRequest.objects.filter(
            product=product,
            status='Pending'
        ).exclude(
            id=exchange.id
        ).select_related('requester')

        for other_request in other_requests:
            other_request.status = 'Rejected'
            other_request.save(update_fields=['status', 'updated_at'])

            Notification.objects.create(
                recipient=other_request.requester,
                message=(
                    f"Your exchange request for {product.name} "
                    f"was rejected because the product has been sold."
                ),
                exchange_request=other_request
            )

    messages.success(
        request,
        'Exchange request accepted! Your product is now marked as Sold.'
    )

    return redirect('dashboard')


# REJECT EXCHANGE REQUEST
@login_required
def reject_exchange_request(request, request_id):
    if request.method != 'POST':
        return redirect('dashboard')

    exchange = get_object_or_404(
        ExchangeRequest,
        id=request_id,
        product__seller=request.user
    )

    if exchange.status != 'Pending':
        messages.warning(
            request,
            'This exchange request has already been processed.'
        )
        return redirect('dashboard')

    exchange.status = 'Rejected'
    exchange.save()

    Notification.objects.create(
        recipient=exchange.requester,
        message=(
            f"Your exchange request for {exchange.product.name} "
            f"has been rejected."
        ),
        exchange_request=exchange
    )

    messages.success(
        request,
        'Exchange request rejected successfully.'
    )

    return redirect('dashboard')


# EDIT PRODUCT
@login_required
def edit_product(request, product_id):
    product = get_object_or_404(
        Product,
        id=product_id,
        seller=request.user
    )

    if request.method == 'POST':
        form = ProductForm(
            request.POST,
            request.FILES,
            instance=product
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                'Your product has been updated successfully!'
            )

            return redirect('dashboard')
    else:
        form = ProductForm(instance=product)

    return render(
        request,
        'marketplace/edit_product.html',
        {
            'form': form,
            'product': product
        }
    )


# DELETE PRODUCT
@login_required
def delete_product(request, product_id):
    product = get_object_or_404(
        Product,
        id=product_id,
        seller=request.user
    )

    if request.method == 'POST':
        product.delete()

        messages.success(
            request,
            'Your product has been deleted successfully!'
        )

        return redirect('dashboard')

    return render(
        request,
        'marketplace/delete_product.html',
        {'product': product}
    )


# STUDENT LOGOUT
def user_logout(request):
    if request.method == 'POST':
        logout(request)

        messages.success(
            request,
            'You have logged out successfully!'
        )

        return redirect('home')

    return redirect('home')


# EDIT PROFILE
@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = ProfileForm(
            request.POST,
            instance=request.user
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                'Your profile has been updated successfully!'
            )

            return redirect('dashboard')
    else:
        form = ProfileForm(instance=request.user)

    return render(
        request,
        'marketplace/edit_profile.html',
        {'form': form}
    )


# CHANGE PASSWORD
@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(
            request.user,
            request.POST
        )

        if form.is_valid():
            user = form.save()

            update_session_auth_hash(request, user)

            messages.success(
                request,
                'Your password has been changed successfully!'
            )

            return redirect('dashboard')
    else:
        form = PasswordChangeForm(request.user)

    return render(
        request,
        'marketplace/change_password.html',
        {'form': form}
    )


# UPDATE PRODUCT STATUS
@login_required
def update_product_status(request, product_id):
    product = get_object_or_404(
        Product,
        id=product_id,
        seller=request.user
    )

    if request.method == 'POST':
        new_status = request.POST.get('status')

        if new_status in dict(Product.STATUS_CHOICES):
            product.status = new_status
            product.save()

            messages.success(
                request,
                f'Product status updated to {new_status}!'
            )
        else:
            messages.error(
                request,
                'Invalid product status!'
            )

    return redirect('dashboard')


# START OR OPEN A CHAT
@login_required
def start_chat(request, product_id):

    product = get_object_or_404(Product, id=product_id)

    if product.seller == request.user:
        messages.error(
            request,
            'You cannot chat with yourself!'
        )
        return redirect('product_detail', product_id=product.id)

    participant_one, participant_two = sorted(
        [request.user, product.seller],
        key=lambda user: user.id
    )

    conversation, created = Conversation.objects.get_or_create(
        product=product,
        participant_one=participant_one,
        participant_two=participant_two
    )

    return redirect(
        'chat_room',
        conversation_id=conversation.id
    )


# CHAT LIST
@login_required
def chat_list(request):
    conversations = Conversation.objects.filter(
        models.Q(participant_one=request.user) |
        models.Q(participant_two=request.user)
    ).select_related(
        'product', 'participant_one', 'participant_two'
    ).order_by('-updated_at')

    total_unread = 0

    for conversation in conversations:
        conversation.last_message = (
            conversation.messages.order_by('-created_at').first()
        )

        conversation.unread_count = conversation.messages.filter(
            is_read=False
        ).exclude(sender=request.user).count()

        total_unread += conversation.unread_count

    return render(
        request,
        'marketplace/chat_list.html',
        {
            'conversations': conversations,
            'total_unread': total_unread,
        }
    )


# CHAT ROOM
@login_required
def chat_room(request, conversation_id):

    conversation = get_object_or_404(
        Conversation.objects.select_related(
            'product',
            'participant_one',
            'participant_two'
        ),
        id=conversation_id
    )

    if request.user not in [
        conversation.participant_one,
        conversation.participant_two
    ]:
        messages.error(
            request,
            'You are not allowed to access this conversation.'
        )
        return redirect('home')

    conversation.messages.filter(
        is_read=False
    ).exclude(
        sender=request.user
    ).update(is_read=True)

    chat_messages = conversation.messages.select_related(
        'sender'
    ).all()

    other_user = (
        conversation.participant_two
        if conversation.participant_one == request.user
        else conversation.participant_one
    )

    return render(
        request,
        'marketplace/chat_room.html',
        {
            'conversation': conversation,
            'chat_messages': chat_messages,
            'other_user': other_user,
        }
    )


# SEND CHAT MESSAGE
@login_required
def send_chat_message(request, conversation_id):

    conversation = get_object_or_404(
        Conversation,
        id=conversation_id
    )

    if request.user not in [
        conversation.participant_one,
        conversation.participant_two
    ]:
        messages.error(
            request,
            'You are not allowed to send messages here.'
        )
        return redirect('home')

    if request.method == 'POST':

        content = request.POST.get('content', '').strip()

        if content:
            ChatMessage.objects.create(
                conversation=conversation,
                sender=request.user,
                content=content
            )

            conversation.save()

    return redirect(
        'chat_room',
        conversation_id=conversation.id
    )


# FETCH NEW CHAT MESSAGES
@login_required
def fetch_chat_messages(request, conversation_id):

    conversation = get_object_or_404(
        Conversation,
        id=conversation_id
    )

    if request.user not in [
        conversation.participant_one,
        conversation.participant_two
    ]:
        return JsonResponse(
            {'error': 'Unauthorized'},
            status=403
        )

    messages_list = conversation.messages.select_related(
        'sender'
    ).order_by('created_at')

    data = []

    for message in messages_list:
        data.append({
            'id': message.id,
            'sender': message.sender.username,
            'content': message.content,
            'created_at': message.created_at.strftime('%d %b %Y, %I:%M %p'),
            'is_me': message.sender_id == request.user.id,
        })

    conversation.messages.filter(
        is_read=False
    ).exclude(
        sender=request.user
    ).update(is_read=True)

    return JsonResponse({'messages': data})


# ADD OR REMOVE PRODUCT FROM WISHLIST
@login_required
def toggle_wishlist(request, product_id):

    if request.method != 'POST':
        return redirect('home')

    product = get_object_or_404(Product, id=product_id)

    if product.seller == request.user:
        messages.warning(
            request,
            'You cannot add your own product to your wishlist.'
        )
        return redirect('home')

    if product.status != 'Available':
        messages.warning(
            request,
            'This product is no longer available.'
        )
        return redirect('home')

    wishlist_item = Wishlist.objects.filter(
        user=request.user,
        product=product
    ).first()

    if wishlist_item:
        wishlist_item.delete()

        messages.success(
            request,
            'Product removed from your wishlist.'
        )
    else:
        Wishlist.objects.create(
            user=request.user,
            product=product
        )

        messages.success(
            request,
            'Product added to your wishlist!'
        )

    return redirect('home')


# MY WISHLIST PAGE
@login_required
def my_wishlist(request):

    wishlist_items = Wishlist.objects.filter(
        user=request.user
    ).select_related(
        'product',
        'product__seller'
    )

    return render(
        request,
        'marketplace/wishlist.html',
        {
            'wishlist_items': wishlist_items,
        }
    )


# REMOVE PRODUCT FROM WISHLIST
@login_required
def remove_from_wishlist(request, product_id):

    if request.method != 'POST':
        return redirect('my_wishlist')

    wishlist_item = get_object_or_404(
        Wishlist,
        user=request.user,
        product_id=product_id
    )

    wishlist_item.delete()

    messages.success(
        request,
        'Product removed from your wishlist.'
    )

    return redirect('my_wishlist')


# SUBMIT SELLER REVIEW
@login_required
def submit_seller_review(request, exchange_id):

    exchange = get_object_or_404(
        ExchangeRequest.objects.select_related(
            'product',
            'product__seller',
            'requester'
        ),
        id=exchange_id,
        requester=request.user
    )

    if exchange.status != 'Accepted':
        messages.error(
            request,
            'You can only review a seller after an exchange is accepted.'
        )
        return redirect(
            'product_detail',
            product_id=exchange.product.id
        )

    if SellerReview.objects.filter(
        exchange_request=exchange
    ).exists():
        messages.warning(
            request,
            'You have already reviewed this seller for this exchange.'
        )
        return redirect(
            'product_detail',
            product_id=exchange.product.id
        )

    if request.method == 'POST':
        form = SellerReviewForm(request.POST)

        if form.is_valid():
            review = form.save(commit=False)
            review.exchange_request = exchange
            review.reviewer = request.user
            review.seller = exchange.product.seller
            review.save()

            messages.success(
                request,
                'Thank you! Your seller review has been submitted.'
            )

            return redirect(
                'product_detail',
                product_id=exchange.product.id
            )
    else:
        form = SellerReviewForm()

    return render(
        request,
        'marketplace/review_seller.html',
        {
            'form': form,
            'exchange': exchange,
        }
    )
