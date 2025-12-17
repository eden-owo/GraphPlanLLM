"""House URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
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

from Houseweb import views

urlpatterns = [
    # path('admin/', admin.site.urls),
    path('index/LoadTestBoundary', views.LoadTestBoundary),
    path('index/NumSearch/', views.NumSearch),
    path(r'index/LoadTrainHouse/', views.LoadTrainHouse),
    path(r'index/TransGraph/', views.TransGraph),
    path(r'index/TransGraph_net/', views.TransGraph_net),
    path(r'index/Init/', views.Init),
    path(r'index/AdjustGraph/', views.AdjustGraph),
    path(r'index/GraphSearch/', views.GraphSearch),
    path(r'index/RelBox/', views.RelBox),
    path(r'index/Save_Editbox/', views.Save_Editbox),

    path('home', views.home_classic),  # Classic 單頁式介面 (預設)
    path('home_wizard', views.home) ,  # Wizard 步驟式介面
    path('home_example', views.home_example),  # Example 範例展示介面
    path('index/GetExampleList/', views.GetExampleList),  # 取得範例列表
    path('index/LLMGenerateGraph/', views.LLMGenerateGraph),  # LLM Graph 生成
    path('index/LLMRegenerateLayout/', views.LLMRegenerateLayout),  # LLM 重新生成佈局
    path('index/LLMSaveLayout/', views.LLMSaveLayout),  # LLM 儲存佈局


]
