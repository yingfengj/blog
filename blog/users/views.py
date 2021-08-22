import re

from django.db import DatabaseError
from django.http import HttpResponseBadRequest, HttpResponse, JsonResponse
from django.shortcuts import render
import logging

# Create your views here.

# 注册视图
from django.views import View
from django_redis import get_redis_connection

from libs.captcha.captcha import captcha
from users.models import User
from utils.response_code import RETCODE

logger=logging.getLogger('django')



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

class RegisterView(View):

    def get(self, request):

        return render(request, 'register.html')

    def post(self, request):
        #
        # 1.接收数据
        mobile = request.POST.get('mobile')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')

        # image_code_client = request.GET.get('image_code')
        # uuid = request.GET.get('uuid')



        # 2.验证数据
        #     2.1参数是否齐全
        # 校验参数
        if not all([mobile,password,password2]):
            return JsonResponse({'code': RETCODE.NECESSARYPARAMERR, 'errmsg': '缺少必传参数'})


        #     2.2手机号的格式是否正确
        if not re.match(r'^1[3-9]\d{9}$',mobile):
            return HttpResponseBadRequest('请输入正确的手机号')

        #     2.3密码是否符合格式
        if not re.match(r'^[0-9a-zA-Z]{8,20}$',password):
            return HttpResponseBadRequest('请输入8-20位密码')

        #     2.4密码和确认密码要一致
        if password != password2:
            return HttpResponseBadRequest('两次密码输入不一致')

        # #     2.5图片验证码是否和redis中的一致
        # # 创建连接到redis的对象
        # redis_conn = get_redis_connection('default')
        # # 提取图形验证码
        # image_code_server = redis_conn.get('img:%s' % uuid)
        # if image_code_server is None:
        #     # 图形验证码过期或者不存在
        #     return JsonResponse({'code': RETCODE.IMAGECODEERR, 'errmsg': '图形验证码失效'})
        # # 删除图形验证码，避免恶意测试图形验证码
        # try:
        #     redis_conn.delete('img:%s' % uuid)
        # except Exception as e:
        #     logger.error(e)
        # # 对比图形验证码
        # image_code_server = image_code_server.decode()  # bytes转字符串
        # if image_code_client.lower() != image_code_server.lower():  # 转小写后比较
        #     return JsonResponse({'code': RETCODE.IMAGECODEERR, 'errmsg': '输入图形验证码有误'})

        # 3.保存法册信息
        # create_user 使用系统的方法对密码进行加密
        try:
            user = User.objects.create_user(username=mobile,
                                            mobile = mobile,
                                            password=password)
        except  DatabaseError as e:
            logger.error(e)
            return HttpResponseBadRequest('注册失败')

        # 4.返回响应跳转到指定页面
        return HttpResponse('注册成功，跳转至首页（未实现）')

class SmsCodeView(View):

    def get(self,request):
        # 接收参数
        image_code_client = request.GET.get('image_code')
        uuid = request.GET.get('uuid')
        mobile=request.GET.get('mobile')

        # 校验参数
        if not all([image_code_client, uuid,mobile]):
            return JsonResponse({'code': RETCODE.NECESSARYPARAMERR, 'errmsg': '缺少必传参数'})

        # 创建连接到redis的对象
        redis_conn = get_redis_connection('default')
        # 提取图形验证码
        image_code_server = redis_conn.get('img:%s' % uuid)
        if image_code_server is None:
            # 图形验证码过期或者不存在
            return JsonResponse({'code': RETCODE.IMAGECODEERR, 'errmsg': '图形验证码失效'})
        # 删除图形验证码，避免恶意测试图形验证码
        try:
            redis_conn.delete('img:%s' % uuid)
        except Exception as e:
            logger.error(e)
        # 对比图形验证码
        image_code_server = image_code_server.decode()  # bytes转字符串
        if image_code_client.lower() != image_code_server.lower():  # 转小写后比较
            return JsonResponse({'code': RETCODE.IMAGECODEERR, 'errmsg': '输入图形验证码有误'})

        return JsonResponse({'code': RETCODE.OK, 'errmsg': '发送短信成功'})