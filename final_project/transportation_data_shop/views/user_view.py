from django.db import DatabaseError, connection
from django.http import JsonResponse
from django.shortcuts import render


def get(request):
  try:
    name = request.session.get('name')
    print(f'name: {name}')
    with connection.cursor() as cursor:
      cursor.execute('SELECT cash FROM users WHERE name = %s', [name])
      result = cursor.fetchone()
      cash = result[0]
      print(f'cash: {cash}')
    user_id = request.session.get('user_id')
    print(f'user_id: {user_id}')
    with connection.cursor() as cursor:
      cursor.execute('SELECT file_name FROM file_names WHERE user_id = %s', [user_id])
      result = cursor.fetchall()
      print(f'result: {result}')
      file_names = [row[0] for row in result]  # 파일 이름만 추출
    print(f'file_names: {file_names}')
    return render(request, 'my_page.html', {'name': name, 'cash': cash, 'file_names': file_names})
  except ValueError as ve:
      # 사용자 입력 관련 예외 처리
      print(f"ValueError 발생: {ve}")
      return JsonResponse({'error': str(ve)}, status=400)

  except DatabaseError as de:
      # 데이터베이스 관련 예외 처리
      print(f"DatabaseError 발생: {de}")
      return JsonResponse({'error': '데이터베이스 오류가 발생했습니다.', 'details': str(de)}, status=500)

  except Exception as e:
      # 일반적인 예외 처리
      print(f"예기치 않은 오류 발생: {e}")
      return JsonResponse({'error': '알 수 없는 오류가 발생했습니다.', 'details': str(e)}, status=500)