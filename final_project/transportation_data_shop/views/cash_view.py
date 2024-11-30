from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import render
from django.db import connection

def charge_cash(request):
    if request.method == 'POST':
        try:
            # 사용자 ID 가져오기
            user_id = request.session.get('user_id')
            if not user_id:
                return JsonResponse({'error': '로그인이 필요합니다.'}, status=403)

            # 충전 금액 가져오기
            amount = int(request.POST.get('amount'))
            if amount <= 0:
                return JsonResponse({'error': '유효한 금액을 입력해주세요.'}, status=400)

            # 데이터베이스에서 잔액 업데이트
            with connection.cursor() as cursor:
                cursor.execute('UPDATE users SET cash = cash + %s WHERE id = %s', [amount, user_id])

            # 성공 메시지와 리다이렉트
            return HttpResponseRedirect('/my-page/')
        except Exception as e:
            return JsonResponse({'error': '충전 중 오류가 발생했습니다.', 'details': str(e)}, status=500)

    return JsonResponse({'error': '잘못된 요청입니다.'}, status=400)
