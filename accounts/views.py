from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView, FormView, View
from .forms import UserRegistrationForm, PhoneLoginForm

# Create your views here.

class RegisterView(CreateView):
    form_class = UserRegistrationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('login')
    
    def form_valid(self, form):
        user = form.save()
        messages.success(self.request, 'Account created successfully. Please log in.')
        return super().form_valid(form)

class LoginView(FormView):
    form_class = PhoneLoginForm
    template_name = 'accounts/login.html'
    success_url = reverse_lazy('home')
    
    def form_valid(self, form):
        phone_number = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
        user = authenticate(username=phone_number, password=password)
        
        if user is not None:
            login(self.request, user)
            messages.success(self.request, 'You have been logged in successfully.')
            return super().form_valid(form)
        else:
            messages.error(self.request, 'Invalid phone number or password.')
            return self.form_invalid(form)

class LogoutView(View):
    def get(self, request):
        logout(request)
        messages.success(request, 'You have been logged out successfully.')
        return redirect('login')
