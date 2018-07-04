from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import redirect
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator
from datetime import datetime


from common.models import Users,Types,Goods

# 公共信息加载函数
def loadinfo(request):
    lists = Types.objects.filter(pid=0)
    context = {'typelist':lists}
    return context

def index(request):
    '''项目前台首页'''
    context = loadinfo(request)

    return render(request,"web/index.html",context)

def lists(request,pIndex=1):
    '''商品列表页'''
    context = loadinfo(request)
    #查询商品信息
    mod = Goods.objects
    mywhere = []
    subType = []
    #判断封装搜索条件
    tid = int(request.GET.get("tid",0))
    if tid > 0:
        list = mod.filter(typeid__in=Types.objects.only('id').filter(pid=tid))
        mywhere.append('tid='+str(tid))
        
        #查询下级分类
        subType = Types.objects.filter(pid=tid)
    else:
        list = mod.filter()

    #执行分页处理
    pIndex = int(pIndex)
    page = Paginator(list,8) #以8条每页创建分页对象
    maxpages = page.num_pages #最大页数
    #判断页数是否越界
    if pIndex > maxpages:
        pIndex = maxpages
    if pIndex < 1:
        pIndex = 1
    list2 = page.page(pIndex) #当前页数据
    plist = page.page_range   #页码数列表

    #封装模板中需要的信息
    context['goodslist'] = list2
    context['plist'] = plist
    context['pIndex'] = pIndex
    context['mywhere'] = mywhere   
    context['subList'] = subType
    return render(request,"web/list.html",context)

def detail(request,gid):
    '''商品详情页'''
    context = loadinfo(request)
    ob = Goods.objects.get(id=gid)
    ob.clicknum += 1
    ob.save()
    context['goods'] = ob
    return render(request,"web/detail.html",context)

# ==============前台会员登录====================
def login(request):
    '''会员登录表单'''
    return render(request,'web/login.html')

def dologin(request):
    '''会员执行登录'''
    # 校验验证码
    verifycode = request.session['verifycode']
    code = request.POST['code']
    if verifycode != code:
        context = {'info':'验证码错误！'}
        return render(request,"web/login.html",context)

    try:
        #根据账号获取登录者信息
        user = Users.objects.get(username=request.POST['username'])
        #判断当前用户是否是后台管理员用户
        if user.state == 0 or user.state == 1:
            # 验证密码
            import hashlib
            m = hashlib.md5() 
            m.update(bytes(request.POST['password'],encoding="utf8"))
            if user.password == m.hexdigest():
                # 此处登录成功，将当前登录信息放入到session中，并跳转页面
                request.session['vipuser'] = user.toDict()
                return redirect(reverse('index'))
            else:
                context = {'info':'登录密码错误！'}
        else:
            context = {'info':'此用户为非法用户！'}
    except:
        context = {'info':'登录账号错误！'}
    return render(request,"web/login.html",context)

def logout(request):
    '''会员退出'''
    # 清除登录的session信息
    del request.session['vipuser']
    # 跳转登录页面（url地址改变）
    return redirect(reverse('login'))

def register(request):
    '''会员注册'''
    return render(request, 'web/register.html')

def regdetail(request):
    '''跳转到注册详细页面，当前操作不更新数据库'''
    username = request.POST["username"]
    password = request.POST["password"]
    repassword = request.POST["repassword"]
    context = { }
    try:
        if password != repassword:
            context = {'info':'两次输入的密码不一致！'}
            raise Exception
        user = Users.objects.filter(username = username)
        if user:
            context = {'info':'当前用户名已经存在！'}
            raise Exception    
        context['username'] = username
        context['password'] = password
        return render(request, 'web/regdetail.html', context)
    except Exception as err:
        print(err)
        return render(request, 'web/register.html', context)


def doregister(request):
    '''会员注册'''
    try:
        ob = Users()
        ob.username = request.POST['username']
        password = request.POST["password"]
        repassword = request.POST["repassword"]
        if password != repassword:
            context = {'info':'两次输入的密码不一致！'}
            raise Exception
        user = Users.objects.filter(username = username)
        if user:
            context = {'info':'当前用户名已经存在！'}
            raise Exception    
        #获取密码并md5
        import hashlib
        m = hashlib.md5() 
        m.update(bytes(request.POST['password'],encoding="utf8"))
        ob.password = m.hexdigest()
        ob.state = 1
        ob.addtime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ob.save()
        request.session['vipuser'] = ob.toDict()
        context={"info":"注册成功！"}
    except Exception as err:
        print(err)
    return render(request,"web/register.html",context)


def usercenter(request):
    if request.session['vipuser']:
        context={"user":request.session['vipuser']}
        print(request.session['vipuser'])
        return render(request, 'web/userdetail.html', context)
    else:
        return redirect(reverse('login'))


def doupdate(request):
    '''会员信息修改'''
    try:
        ob = Users.objects.get(username=request.POST['username'])
        ob.username = request.POST['username']
        ob.name = request.POST['name']
        ob.sex = request.POST['sex']
        ob.address = request.POST['address']
        ob.code = request.POST['code']
        ob.phone = request.POST['phone']
        ob.email = request.POST['email']
        ob.state = 1
        ob.save()
        request.session['vipuser'] = ob.toDict()
        context = {"info":"修改成功！", "user":request.session['vipuser']}
        
    except Exception as err:
        print(err)
        context={"info":"修改失败"}
    return render(request,"web/userdetail.html",context)

def resetpassword(request):
    if request.session['vipuser']:
        context={"user":request.session['vipuser']}
        return render(request, 'web/resetpassword.html', context)
    else:
        return redirect(reverse('login'))

def doresetpassword(request):
    '''修改密码'''
    ob = Users.objects.get(username=request.POST['username'])
    password = request.POST["orgpassword"]
    newpassword = request.POST["password"]
    repassword = request.POST["repassword"]
    context = { }
    try:
        if password == "":
            context = {'info':'请输入密码！'}
            raise Exception 

        if newpassword == "":
            context = {'info':'请输入新密码！'}
            raise Exception 

        if repassword == "":
            context = {'info':'请输入确认密码！'}
            raise Exception 

        #判断密码是否正确
        import hashlib
        m = hashlib.md5() 
        m.update(bytes(password,encoding="utf8"))
        
        if ob.password != m.hexdigest():
            context = {'info':'密码输入错误'}
            raise Exception    
        
        if newpassword != repassword:
            context = {'info':'两次输入的密码不一致！'}
            raise Exception

        m.update(bytes(newpassword,encoding="utf8"))
        ob.password = m.hexdigest()
        ob.save()
        context = {'info':'密码修改成功！'}
        return render(request, 'web/resetpassword.html', context)
    except Exception as err:
        print(err)       
        context['user'] = ob
        return render(request, 'web/resetpassword.html', context)