
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class Product(models.Model):

    CATEGORY_CHOICES = [
        ('Books', 'Books'),
        ('Electronics', 'Electronics'),
        ('Notes', 'Notes'),
        ('Accessories', 'Accessories'),
        ('Others', 'Others'),
    ]

    STATUS_CHOICES = [
        ('Available', 'Available'),
        ('Sold', 'Sold'),
    ]

    seller = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    name = models.CharField(max_length=200)

    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES
    )

    description = models.TextField()

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    image = models.ImageField(
        upload_to='products/'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Available'
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.name


# WISHLIST MODEL
class Wishlist(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='wishlist_items'
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='wishlisted_by'
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'product'],
                name='unique_user_wishlist_product'
            )
        ]

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"


# RECENTLY VIEWED MODEL
class RecentlyViewed(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recently_viewed_products'
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='viewed_by_students'
    )

    viewed_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ['-viewed_at']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'product'],
                name='unique_recently_viewed_product'
            )
        ]

    def __str__(self):
        return f"{self.user.username} viewed {self.product.name}"


# EXCHANGE REQUEST MODEL
class ExchangeRequest(models.Model):

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Accepted', 'Accepted'),
        ('Rejected', 'Rejected'),
    ]

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='exchange_requests'
    )

    requester = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_exchange_requests'
    )

    message = models.TextField(
        blank=True,
        help_text="Write a message to the seller (optional)."
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Pending'
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['product', 'requester'],
                name='unique_exchange_request_per_student'
            )
        ]

    def __str__(self):
        return f"{self.requester.username} - {self.product.name} ({self.status})"


# SELLER REVIEW MODEL
class SellerReview(models.Model):

    exchange_request = models.OneToOneField(
        ExchangeRequest,
        on_delete=models.CASCADE,
        related_name='review'
    )

    reviewer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='given_seller_reviews'
    )

    seller = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='received_seller_reviews'
    )

    rating = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5)
        ]
    )

    comment = models.TextField(
        max_length=500,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.reviewer.username} rated {self.seller.username} - {self.rating}/5"


# NOTIFICATION MODEL
class Notification(models.Model):

    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications'
    )

    message = models.CharField(max_length=255)

    exchange_request = models.ForeignKey(
        ExchangeRequest,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications'
    )

    is_read = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.recipient.username} - {self.message}"


# CHAT CONVERSATION MODEL
class Conversation(models.Model):

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='conversations'
    )

    participant_one = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='conversations_as_one'
    )

    participant_two = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='conversations_as_two'
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ['-updated_at']
        constraints = [
            models.UniqueConstraint(
                fields=[
                    'product',
                    'participant_one',
                    'participant_two'
                ],
                name='unique_product_conversation'
            )
        ]

    def __str__(self):
        return f"{self.participant_one.username} - {self.participant_two.username}"


# CHAT MESSAGE MODEL
class ChatMessage(models.Model):

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )

    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_chat_messages'
    )

    content = models.TextField()

    is_read = models.BooleanField(default=False)

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.sender.username}: {self.content[:30]}"
