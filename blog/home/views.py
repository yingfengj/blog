from django.shortcuts import render
from home.models import ArticleCategory, Article
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

        # 查询分类数据
        categories = Article.objects.all()

        # 组织模板数据传递，渲染
        context = {
            'categories': categories,
            'category': article.category,
            'article': article,
        }

        return render(request, 'detail.html', context=context)