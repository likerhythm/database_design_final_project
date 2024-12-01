from django.db import connection
from django.http import HttpResponse
from django.shortcuts import redirect, render

def user_exists(login_id, password):
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM users WHERE login_id = %s and password = %s", [login_id, password])
        result = cursor.fetchone()
        return result[0] > 0

def login_view(request):
    if request.method == 'POST':
        login_id = request.POST.get('login_id')
        password = request.POST.get('password')

        if user_exists(login_id, password):
            with connection.cursor() as cursor:
              cursor.execute("SELECT name, id FROM users WHERE login_id = %s and password = %s", [login_id, password])
              result = cursor.fetchone()
              name = result[0]  # name 값 추출
              id = result[1]
            # 로그인 성공
            context = {
                'name': name,
            }
            request.session['name'] = name
            request.session['user_id'] = id
            return render(request, 'main.html', context)  # main.html로 리다이렉트
        else:
            # 로그인 실패
            return HttpResponse("Invalid username or password")
    return render(request, 'login.html')

def register_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        login_id = request.POST.get('login_id')
        password = request.POST.get('password')

        # 데이터베이스에 사용자 삽입
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO users (name, login_id, password, cash) VALUES (%s, %s, %s, %s)",
                [name, login_id, password, 0]
            )
            cursor.execute("SELECT LAST_INSERT_ID()")
            user_id = cursor.fetchone()[0]
            cursor.execute(
                "INSERT INTO carts (user_id) VALUES (%s)",
                [user_id]
            )
        return redirect('login')  # 회원가입 후 로그인 페이지로 리다이렉트

    return render(request, 'register.html')  # GET 요청일 경우 회원가입 페이지 렌더링

def logout(request):
    request.session.flush()
    return redirect('/')