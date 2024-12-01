"""
URL configuration for final_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from transportation_data_shop import views
from transportation_data_shop.views import auth_view
from transportation_data_shop.views import main_view
from transportation_data_shop.views import cart_view
from transportation_data_shop.views import user_view
from transportation_data_shop.views import download_view
from transportation_data_shop.views import cash_view
from transportation_data_shop.views.views import SubwayView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('subway-view/', SubwayView.as_view(), name='subway_view'),
    path('login/', auth_view.login_view, name='login'),  # 로그인 페이지
    path('register/', auth_view.register_view, name='register'),  # 회원가입 페이지
    path('', main_view.main, name='main'),  # 메인 페이지 (추가 필요)
    path('cart/', cart_view.get_cart, name='cart'),
    path('add-to-cart/', views.views.add_to_cart, name='add_to_cart'),
    path('submit-selected-items/', cart_view.purchase, name='purchase'),
    path('my-page/', user_view.get, name='my_page'),  # 마이페이지
    path('download/<str:file_name>/', download_view.download_file, name='download_file'),
    path('charge-cash/', cash_view.charge_cash, name='charge_cash'),
    path('logout/', auth_view.logout, name='logout'),
]
