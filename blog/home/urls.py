#
# @author：浊浪
# @version：0.1
# @time： 2021/8/23 21:32
# 
from django.urls import path
from home.views import IndexView,DetailView
urlpatterns = [
    # 首页的路由
    path('', IndexView.as_view(), name = 'index'),

    # 文章详情路由
    path('detail/',DetailView.as_view(), name = 'detail'),

]