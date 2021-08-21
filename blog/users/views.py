from django.http import HttpResponseBadRequest, HttpResponse
from django.shortcuts import render

# Create your views here.

# 注册视图
from django.views import View
from django_redis import get_redis_connection

from libs.captcha.captcha import captcha


class RegisterView(View):

    def get(self, request):

        return render(request, 'register.html')


class ImageCodeView(View):

    def get(self, request):
        '''
        1.接收前端传递过来的uuid
        2.判断uid是否获取到
        3.通过调用captcha 来生成图片验证码（图片二进制和图片内容）
        4将图片内容保存到redis中
        uuid作为一个key，图片内容作为一个value同时我们还需要设置一个实效
        5.返回图片二进制
        '''

        # 获取前端传递过来的参数
        uuid = request.GET.get('uuid')
        # 判断参数是否为None
        if uuid is None:
            return HttpResponseBadRequest('请求参数错误')
        # 获取验证码内容和验证码图片二进制数据
        text, image = captcha.generate_captcha()
        # 将图片验内容保存到redis中，并设置过期时间
        redis_conn = get_redis_connection('default')
        # key 设置为uuid
        # seconds 过期秒数300秒5分钟过期时间
        # value text
        redis_conn.setex('img:%s' % uuid, 300, text)
        # 返回响应，将生成的图片以content_type为image/jpeg的形式返回给请求
        return HttpResponse(image, content_type='image/jpeg')

