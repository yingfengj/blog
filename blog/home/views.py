from django.shortcuts import render, redirect
from django.urls import reverse

from home.models import ArticleCategory, Article, Comment
from django.http.response import HttpResponseNotFound

# Create your views here.
from django.views import View


class IndexView(View):
    def get(self, request):

        # 接收所有分类信息
        categories = ArticleCategory.objects.all()

        # 接收用户 点击的分类id
        cat_id = request.GET.get('cat_id',1)

        # 根据分类id进行分类的查询
        try:
            category = ArticleCategory.objects.get(id = cat_id)
        except ArticleCategory.DoesNotExist:
            return HttpResponseNotFound('没有此分类')

        # 获取分页参数
        page_num = request.GET.get('page_num', 1)
        page_size = request.GET.get('page_size', 10)

        # 根据分类查询文章数据
        articles = Article.objects.filter(category=category)

        # 创建分页器
        from django.core.paginator import Paginator,EmptyPage
        paginator = Paginator(articles,per_page=page_size)

        # 进行分页处理
        try:
            page_articles = paginator.page(page_num)
        except EmptyPage:
            return HttpResponseNotFound('empty page')
        # 总页数
        total_page = paginator.num_pages

        # 组织数据传递给模板渲染
        context = {
            'categories': categories,
            'category': category,
            'articles': articles,
            'page_size': page_size,
            'total_page': total_page,
            'page_num': page_num
        }


        return render(request,'index.html',context=context)

class DetailView(View):

    def get(self,request):

        # 接收文章id信息
        id = request.GET.get('id')

        # 根据文章id进行文章数据查询
        try:
            article = Article.objects.get(id = id)
        except Article.DoesNotExist:
            return render(request, '404.html')
        else:
            # 浏览量+1
            article.total_views += 1
            article.save()

        # 查询分类数据
        categories = ArticleCategory.objects.all()

        # 查询浏览量前十的文章,若没有十篇就全列出来
        hot_articles =Article.objects.order_by('-total_views')[0:10] if len(
            Article.objects.order_by('total_views'))>=10 else Article.objects.order_by(
            '-total_views')

        # 获取分页请求参数
        page_num = request.GET.get('page_num', 1)
        page_size = request.GET.get('page_size', 5)

        # 根据文章信息查询评论数据
        comments = Comment.objects.filter(article=article).order_by('-created')

        # 获取评论总数
        total_count = comments.count()

        # 创建分页器
        from django.core.paginator import Paginator,EmptyPage
        paginator = Paginator(comments,page_size)

        # 进行分页处理
        try:
            page_comments = paginator.page(page_num)
        except EmptyPage:
            return HttpResponseNotFound('empty page')

        # 总页数
        total_page = paginator.num_pages

        # 组织模板数据传递，渲染
        context = {
            'categories': categories,
            'category': article.category,
            'article': article,
            'hot_articles': hot_articles,
            'total_count': total_count,
            'total_page': total_page,
            'comments': page_comments,
            'page_num': page_num,
            'page_size': page_size
        }

        return render(request, 'detail.html', context=context)

    def post(self,request):
        # 1.接收用户信息
        user = request.user

        # 2.判断用户是否登录
        if user and user.is_authenticated:

        # 3.登录的用户就可以接收form数据

            # 3.1接收用户评论数据
            id = request.POST.get('id')
            content = request.POST.get('content')

            # 3.2验证文章是否存在
            try:
                article = Article.objects.get(id=id)
            except Article.DoesNotExist:
                return HttpResponseNotFound('没有此文章')

            # 3.3保存评论数据
            Comment.objects.create(
                content=content,
                article=article,
                user=user
            )

            # 3.4修改文章评论数量
            article.comments_count += 1
            article.save()

            # 刷新当前页面
            path = reverse('home:detail')+f'?id={article.id}'
            return redirect(path)
        # 4.未登录用户就跳转到登录页面
        else:
            return redirect(reverse('users:login'))

        pass