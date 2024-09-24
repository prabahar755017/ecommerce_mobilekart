from django.db import models
from django.contrib.auth.models import User
import datetime
import os
from django.utils import timezone
 
def getFileName(requset,filename):
  now_time=datetime.datetime.now().strftime("%Y%m%d%H:%M:%S")
  new_filename="%s%s"%(now_time,filename)
  return os.path.join('uploads/',new_filename)
 
class Category(models.Model):
  name=models.CharField(max_length=150,null=False,blank=False)
  image=models.ImageField(upload_to=getFileName,null=True,blank=True)
  description=models.TextField(max_length=500,null=False,blank=False)
  status=models.BooleanField(default=False,help_text="0-show,1-Hidden")
  created_at=models.DateTimeField(auto_now_add=True)
 
  def __str__(self) :
    return self.name
 
class Product(models.Model):
  category=models.ForeignKey('ecommerce_app.Category',on_delete=models.CASCADE)
  name=models.CharField(max_length=150,null=False,blank=False)
  vendor=models.CharField(max_length=150,null=False,blank=False)
  product_image=models.ImageField(upload_to=getFileName,null=True,blank=True)
  quantity=models.IntegerField(null=False,blank=False)
  original_price=models.FloatField(null=False,blank=False)
  selling_price=models.FloatField(null=False,blank=False)
  description=models.TextField(max_length=500,null=False,blank=False)
  status=models.BooleanField(default=False,help_text="0-show,1-Hidden")
  trending=models.BooleanField(default=False,help_text="0-default,1-Trending")
  created_at=models.DateTimeField(auto_now_add=True)
 
  def __str__(self) :
    return self.name




class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)  
    session_id = models.CharField(max_length=255, null=True, blank=True)  
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    product_qty = models.IntegerField(null=False, blank=False)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.product.name} - {self.product_qty}"
    @property
    def total_cost(self):
          return self.product_qty*self.product.selling_price
      


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE,null=True, blank=True)  # Link order to the registered user
    order_date = models.DateTimeField(auto_now_add=True)
    is_paid = models.BooleanField(default=False)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    shipping_address = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Order {self.id} by {self.user.username}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2,blank=True, null=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2,blank=True, null=True)

    def get_total(self):
        return self.unit_price * self.quantity

    def __str__(self):
        return f'{self.product.name} - {self.quantity}'




class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('cashondelivery', 'CashOnDelivery'),
    ]
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    payment_date = models.DateTimeField(auto_now_add=True)
    payment_status = models.BooleanField(default=False)
    amount = models.DecimalField(max_digits=10, decimal_places=2,blank=True, null=True)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    transaction_id = models.CharField(max_length=255, blank=True, null=True)


    def __str__(self):
        return f"Payment for Order {self.order.id}"


class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    name = models.CharField(max_length=100)
    street = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=10)

    def __str__(self):
        return f"{self.name}, {self.street}, {self.city}, {self.state}, {self.zip_code}"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_image = models.ImageField(upload_to=getFileName, null=True,blank=True)

    def __str__(self):
        return self.user.username
