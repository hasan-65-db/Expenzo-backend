from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.db.models import Q, Sum
from .models import User, Transaction, Budget
from .serializer import (
    UserCreateSerializer,
    UserResponseSerializer,
    TransactionCreateSerializer,
    TransactionResponseSerializer,
    BudgetCreateSerializer
    
)
from .oauth2 import get_password_hash, get_password_verify, create_access_token
from .redis_client import redis_client
import json
from django_filters import rest_framework as filters
from django_filters.rest_framework import DjangoFilterBackend
import hashlib
from .tasks import send_registration_mail
import logging
from .tasks import budgetAlertMail
from rest_framework.exceptions import PermissionDenied

class Register(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = UserCreateSerializer(data=request.data)
        if serializer.is_valid():
            user = User.objects.create(
                email = serializer.validated_data['email'],
                password = get_password_hash(serializer.validated_data['password'])
            )
            send_registration_mail.delay(user.email)
            return Response(UserResponseSerializer(user).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
class Login(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"detail": "Invalid credentials"}, status=404)
        if not get_password_verify(password,user.password):
            return Response({"detail":"Invalid credentials"}, status=404)
        
        return Response({
            "access_token":create_access_token(user.id),
            "token_type":"bearer"
        })
    
class TransactionFilter(filters.FilterSet):
    search = filters.CharFilter(field_name="title", lookup_expr="icontains")
    min_price = filters.NumberFilter(field_name="amount", lookup_expr='gte')
    max_price = filters.NumberFilter(field_name="amount", lookup_expr='lte')
    start_date = filters.DateFilter(field_name="created_at", lookup_expr="date__gte")
    end_date = filters.DateFilter(field_name="created_at", lookup_expr="date__lte")

    class Meta:
        model=Transaction
        fields = ['category']


# class ExpenseListCreateView(generics.ListCreateAPIView):
#     permission_classes = [IsAuthenticated]
#     filterset_class = TransactionFilter
#     filter_backends = [DjangoFilterBackend]

#     def get_serializer_class(self):
#         if self.request.method == "POST":
#             return TransactionCreateSerializer
#         return TransactionResponseSerializer
    
#     def get_queryset(self):
#         return Transaction.objects.filter(owner=self.request.user)

#     def list(self, request):
#         query_params = request.query_params.urlencode()
#         query_hash = hashlib.md5(query_params.encode()).hexdigest()
#         cache_key = f"expenses_user_{request.user.id}_{query_hash}"
#         cached = redis_client.get(cache_key)
#         if cached:
#             return Response(json.loads(cached))
#         queryset = self.filter_queryset(self.get_queryset())
#         serializer = self.get_serializer(queryset, many=True)
#         redis_client.setex(cache_key, 300, json.dumps(serializer.data))
#         return Response(serializer.data)
    
#     def perform_create(self, serializer):
#         expense = serializer.save(owner=self.request.user)
#         redis_client.delete(f"expenses_user_{self.request.user.id}")


class BudgetCreateView(generics.CreateAPIView):
    queryset = Budget.objects.all()
    serializer_class = BudgetCreateSerializer
    permission_classes = [IsAuthenticated]
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

class ExpenseListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    filterset_class = TransactionFilter
    filter_backends = [DjangoFilterBackend]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return TransactionCreateSerializer
        return TransactionResponseSerializer
    def get_queryset(self):
        return Transaction.objects.filter(owner=self.request.user)
    
    def list(self, request):
        query_params = request.query_params.urlencode()
        query_hash = hashlib.md5(query_params.encode()).hexdigest()
        cache_key = f"expenses_user_{request.user.id}_{query_hash}"
        cached = redis_client.get(cache_key)
        if cached:
            return Response(json.loads(cached))
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        redis_client.setex(cache_key, 300, json.dumps(serializer.data))
        return Response(serializer.data)
    
    def perform_create(self, serializer):
        expense = serializer.save(owner=self.request.user)
        pattern = f"expenses_user_{self.request.user.id}_*"
        keys_to_delete = redis_client.keys(pattern)
        if keys_to_delete:
            redis_client.delete(*keys_to_delete)
        self.check_budget_limit(self.request.user)

    def check_budget_limit(self, user):
        try:
            budget = Budget.objects.get(owner=user)
            total_spent = Transaction.objects.filter(owner=user).aggregate(Sum('amount'))['amount__sum'] or 0
            if total_spent >= (float(budget.monthly_limit)*0.8):
                budgetAlertMail.delay(user.email)
        except Budget.DoesNotExist:
            pass

class ExpenseDetailView(generics.RetrieveUpdateDestroyAPIView):
    http_method_names = ['get', 'put', 'delete']
    permission_classes = [IsAuthenticated]
    serializer_class = TransactionCreateSerializer
    lookup_field = 'id'

    def get_serializer_class(self):
        if self.request.method == "PUT":
            return TransactionCreateSerializer
        return TransactionResponseSerializer

    def get_queryset(self):
        return Transaction.objects.filter(owner=self.request.user)
    
    def get_object(self):
        obj = super().get_object()
        if obj.owner_id != self.request.user.id:
            raise PermissionDenied("Not authorized to perform this action")
        return obj
    def perform_destroy(self, instance):
        pattern = f"expenses_user_{self.request.user.id}_*"
        keys = redis_client.keys(pattern)
        if keys:
            redis_client.delete(*keys)
        instance.delete()

    def perform_update(self, serializer):
        serializer.save()
        pattern = f"expenses_user_{self.request.user.id}_*"
        keys = redis_client.keys(pattern)
        if keys:
            redis_client.delete(*keys)