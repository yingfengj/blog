import re

from django.db import DatabaseError
from django.http import HttpResponseBadRequest, HttpResponse, JsonResponse
from django.shortcuts import render
import logging
from django.shortcuts import redirect
from django.urls import reverse

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

        from django.contrib.auth import login
        login(request, user)

        # 4.返回响应跳转到指定页面
        # redirect 是进行重定向
        # reverse是可以通过namespace:name 来获取到视图所对应的路由
        response =  redirect(reverse('home:index'))
        # return HttpResponse('注册成功，跳转至首页（未实现）')

        # 设置cookie信息，以方便首页中用户信息展示的判断和用户信息的展示
        response.set_cookie('is_login', True)
        response.set_cookie('username', user.username, max_age= 7*24*3600)

        return response


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

class LoginView(View):
    def get(self, request):

        return render(request, 'login.html')

    def post(self, request):

        # 1.接收参数
        mobile = request.POST.get('mobile')
        password = request.POST.get('password')
        remember = request.POST.get('remember')

        # 2.校验参数
        # 判断参数是否齐全
        if not all([mobile, password]):
            return HttpResponseBadRequest('缺少必传参数')

        # 判断手机号是否正确
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return HttpResponseBadRequest('请输入正确的手机号')

        # 判断密码是否是8-20个数字
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return HttpResponseBadRequest('密码最少8位，最长20位')

        # 3.用户认证登录
        # 采用系统自带的认证方法进行认证
        # 如果我们的用户名和密码正确，会返user
        # 如果我们的用户名或密码不正确，会返回None
        from django.contrib.auth import authenticate,login
        # 新认的认证方法是针对于username字段进行用户名的判断
        # 当前的判断信息是手机号，所以我们需要修改一下认证字段
        # 我们需要到User模型中进行修改，等测试出现问题的时候，我们再修改
        user = authenticate(mobile=mobile,password=password)
        if user is None:
            return HttpResponseBadRequest('用户名或者密码错误')

        # 4.状态的保持
        login(user=user,request=request)
        response = redirect(reverse('home:index'))
        # 5.根据用户选择的是否记住登录状态来进行判断
        # 6.为了首页显示我们需要设置一些cookie信息
        if remember != 'on':  # 无记住
            # 浏览器关闭之后
            request.session.set_expiry(0)
            response.set_cookie('is_login', True)
            response.set_cookie('username', user.username, max_age=14 * 24 * 3600)
        else:
            # 默认记住两周
            request.session.set_expiry(None)
            response.set_cookie('is_login', True,max_age=14 * 24 * 3600)
            response.set_cookie('username', user.username, max_age=14 * 24 * 3600)


        # 7.返回响应
        return response

from  django.contrib.auth import logout

class LogoutView(View):

    def get(self,request):
        # 1.seession的删除
        logout(request)

        # 2.删除部分session数据
        # response = redirect(reverse('home:index'))
        response = render(request, 'index.html')
        response.delete_cookie('is_login')

        # 3.跳转到首页
        return response

class ForgetPasswordView(View):

    def get(self, request):

        return render(request, 'forget_password.html')

    def post(self, request):
        # 接收参数
        mobile = request.POST.get('mobile')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        # smscode = request.POST.get('sms_code')

        # 判断参数是否齐全
        if not all([mobile, password, password2]):
            return HttpResponseBadRequest('缺少必传参数')

        # 判断手机号是否合法
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return HttpResponseBadRequest('请输入正确的手机号码')

        # 判断密码是否是8-20个数字
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return HttpResponseBadRequest('请输入8-20位的密码')

        # 判断两次密码是否一致
        if password != password2:
            return HttpResponseBadRequest('两次输入的密码不一致')

        # 验证短信验证码
        # redis_conn = get_redis_connection('default')
        # sms_code_server = redis_conn.get('sms:%s' % mobile)
        # if sms_code_server is None:
        #     return HttpResponseBadRequest('短信验证码已过期')
        # if smscode != sms_code_server.decode():
        #     return HttpResponseBadRequest('短信验证码错误')

        # 根据手机号查询数据
        try:
            user = User.objects.get(mobile=mobile)
        except User.DoesNotExist:
            # 如果该手机号不存在，则注册个新用户
            try:
                User.objects.create_user(username=mobile, mobile=mobile,
                                         password=password)
            except Exception:
                return HttpResponseBadRequest('修改失败，请稍后再试')
        else:
            # 修改用户密码
            user.set_password(password)
            user.save()

        # 跳转到登录页面
        response = redirect(reverse('users:login'))

        return response