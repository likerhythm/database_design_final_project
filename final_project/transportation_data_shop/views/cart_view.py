import json
import os
from django.db import connection
from django.http import JsonResponse
from django.shortcuts import render
from django.db import transaction

# Mock 데이터 예제
CART_ITEMS = {
    1: ["Item A", "Item B", "Item C"],
    2: ["Item D", "Item E"],
    # user_id별 장바구니 데이터
}

def get_cart(request):
    # 장바구니 아이템 가져오기 (사용자별로)
    user_id = request.session.get('user_id')
    with connection.cursor() as cursor:
      cursor.execute("SELECT id FROM carts WHERE user_id = %s", [user_id])
      result = cursor.fetchone()
    cart_id = result[0]
    request.session['cart_id'] = cart_id
    print(f'cart_id: {cart_id}')  # 디버깅용 출력

    with connection.cursor() as cursor:
      cursor.execute(
          "SELECT `lines`, districts, custom_name, cost FROM cart_products WHERE cart_id = %s", [cart_id]
      )
      products = cursor.fetchall()
      product_list = [
        {
            'lines': product[0],
            'districts': product[1],
            'custom_name': product[2],
            'cost': product[3],
        }
        for product in products
      ]

    # 렌더링
    return render(request, 'cart.html', 
                  {
                     'name': request.session.get('name'),
                      'product_list': product_list,
                  })

def purchase(request):
  if request.method == 'POST':
    try:
      # 요청 데이터 디코딩 및 JSON 파싱
      data = json.loads(request.body)
      items = data.get('items', [])

      if not items:
        return JsonResponse({'error': '선택된 항목이 없습니다.'}, status=400)
      
      print(f'items: {items}')
      user_id = request.session.get('user_id')

      json_data_list = []

      with transaction.atomic():

        with connection.cursor() as cursor:
                    cursor.execute('SELECT cash FROM users WHERE id = %s', [user_id])
                    user_data = cursor.fetchone()
                    if not user_data:
                        return JsonResponse({'error': '사용자 정보를 찾을 수 없습니다.'}, status=404)
                    user_cash = user_data[0]
                    print(f"사용자 현재 잔액: {user_cash}")

        total_cost = 0
        for item in items:
           cost = item.get('cost')
           total_cost += cost

        if user_cash < total_cost:
           return JsonResponse(
                        {'error': '잔액 부족', 'message': f'{total_cost - user_cash}캐시가 부족합니다.'},
                        status=400
                    )

        for item in items:
          custom_name = item.get('custom_name')
          cost = item.get('cost')

          json_data = make_json(custom_name)
          json_data_list.append(json_data)

          with connection.cursor() as cursor:
            cursor.execute('DELETE FROM cart_products WHERE custom_name = %s', [custom_name])
            cursor.execute('UPDATE users SET cash = cash - %s WHERE id = %s', [cost, user_id])
          print(f"구매 항목: 별칭={custom_name}, 가격={cost}원")
      
        print('구매 완료')
        # 남아 있는 장바구니 데이터를 가져오기
        try:
          with connection.cursor() as cursor:
            cart_id = request.session.get('cart_id')
            cursor.execute('SELECT custom_name, cost, `lines`, districts FROM cart_products WHERE cart_id = %s', [cart_id])
            product_list = cursor.fetchall()
        except Exception as e:
          # 기타 예외 처리
          print(f"Unexpected Error: {e}")
          return JsonResponse({'error': '요청 처리 중 알 수 없는 오류가 발생했습니다.', 'details': str(e)}, status=500)
        print('남은 항목 가져오기')

        try:
          # 저장 디렉토리 확인 및 생성
          user_id = request.session.get('user_id')
          output_directory = f"files/{user_id}"
          os.makedirs(output_directory, exist_ok=True)

          # JSON 파일 저장
          for json_data in json_data_list:
              output_filename = f"{output_directory}/{custom_name}.json"
              with open(output_filename, "w", encoding="utf-8") as json_file:
                  json.dump(json_data, json_file, ensure_ascii=False, indent=4)
              
              # 파일 이름 db에 저장
              with connection.cursor() as cursor:
                cursor.execute('INSERT INTO file_names (user_id, file_name) VALUES (%s, %s)', [user_id, custom_name])
              print(f"JSON 파일이 생성되었습니다: {output_filename}")
        except FileNotFoundError as e:
            print(f"파일 저장 실패: 디렉토리가 존재하지 않습니다. {e}")
        except PermissionError as e:
            print(f"파일 저장 실패: 권한이 없습니다. {e}")
        except Exception as e:
            print(f"예기치 않은 오류가 발생했습니다: {e}")
      return JsonResponse({
        'message': '선택된 항목이 성공적으로 처리되었습니다.',
        'product_list': [
          {'custom_name': row[0], 'cost': row[1], 'lines': row[2], 'districts': row[3]} 
          for row in product_list
        ]
      }, status=200)
      # return JsonResponse({'message': '선택된 항목이 성공적으로 처리되었습니다.'}, status=200)

    except json.JSONDecodeError as e:
      return JsonResponse({'error': '잘못된 JSON 형식입니다.', 'details': str(e)}, status=400)
    except Exception as e:
      return JsonResponse({'error': '요청 처리 중 오류가 발생했습니다.', 'details': str(e)}, status=500)

  # POST 요청이 아닌 경우
  return JsonResponse({'error': '잘못된 요청입니다.'}, status=400)

def make_json(custom_name):
    with connection.cursor() as cursor:
      cursor.execute('SELECT `lines`, districts FROM cart_products WHERE custom_name = %s', [custom_name])
      result = cursor.fetchone()
      lines = result[0]
      districts = result[1]
      line_list = lines.split(',')
      district_list = districts.split(',')
      query = 'SELECT * FROM subway_stations WHERE `line` IN %s and `district` IN %s'
      cursor.execute(query, [tuple(line_list), tuple(district_list)])
      filtered_stations = cursor.fetchall()

      stations_data = []
      for station in filtered_stations:
        station_info = {
            "id": station[0],
            "name": station[1],
            "line": station[2],
            "latitude": station[3],
            "longitude": station[4],
            "district": station[5],
        }
        stations_data.append(station_info)
    return stations_data
