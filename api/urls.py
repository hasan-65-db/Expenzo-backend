from django.urls import path
from . import views

urlpatterns = [
    path("users/", views.Register.as_view()),
    path("login", views.Login.as_view()),
    path("budget/", views.BudgetCreateView.as_view()),
    path("expenses/", views.ExpenseListCreateView.as_view()),
    path("expenses/<int:id>/", views.ExpenseDetailView.as_view()),
]