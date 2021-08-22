#
# @author：浊浪
# @version：0.1
# @time： 2021/8/20 9:25
#
# 进行users 子应用的视图路由

from django.urls import path
from users.views import RegisterView,ImageCodeView,SmsCodeView
urlpatterns = [
    # path 第一个参数：路由
    # path 第二个参数：视图函数名
    path('register/', RegisterView.as_view(), name = 'register'),
    path('imagecode/',ImageCodeView.as_view(), name = 'imagecode'),
    path('smscode/',SmsCodeView.as_view(), name = 'smscode'),
]