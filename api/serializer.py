from rest_framework import serializers
from api.models import User, Transaction, Budget

class TransactionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ["title", "amount", "category"]

class TransactionResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        # fields = ["id", "owner_id"]
        fields = "__all__"
    
class UserCreateSerializer(serializers.ModelSerializer):
    class Meta:
         model = User
         fields = ["email", "password"]

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User already registered on this email")
        return value

class UserResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email"]

class BudgetCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Budget
        fields = [ 'monthly_limit']
        
    def validate_monthly_limit(self, value):
            if value <= 0:
                raise serializers.ValidationError("Monthly limit must be positive number")
            return value
           
