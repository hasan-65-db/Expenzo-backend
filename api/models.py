from django.db import models


class User(models.Model):
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)

    @property
    def is_authenticated(self):
        return True

    def __str__(self):
        return self.email
    
class Budget(models.Model):
    owner = models.OneToOneField(User, on_delete=models.CASCADE,related_name='budget')
    monthly_limit = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.owner.email}'s Budget"

class Transaction(models.Model):
    title = models.CharField(max_length=50)
    amount = models.FloatField()
    category = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    is_recurring = models.BooleanField(default=False)
    next_occurence = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.title
        