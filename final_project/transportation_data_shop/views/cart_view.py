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
        with connection.cursor() as cursor:
            for item in items:
                    custom_name = item.get('custom_name')
                    cost = item.get('cost')

                    # JSON 데이터 생성
                    station_data, edge_data = make_json(custom_name)
                    json_data = {
                        'name': custom_name,
                        'stations': station_data,
                        'edges': edge_data,
                    }
                    # print(json_data)
                    json_data_list.append(json_data)

                    # 데이터베이스 작업
                    cursor.execute('DELETE FROM cart_products WHERE custom_name = %s', [custom_name])
                    cursor.execute('UPDATE users SET cash = cash - %s WHERE id = %s', [cost, user_id])

                    # 성공 메시지 출력
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

          print(f'json_data_list: {json_data_list}')
          # JSON 파일 저장
          for json_data in json_data_list:
              output_filename = f"{output_directory}/{json_data['name']}.json"
              with open(output_filename, "w", encoding="utf-8") as json_file:
                  print('json 파일 저장')
                  json.dump(json_data, json_file, ensure_ascii=False, indent=4)
              
              # 파일 이름 db에 저장
              with connection.cursor() as cursor:

                cursor.execute('INSERT INTO file_names (user_id, file_name) VALUES (%s, %s)', [user_id, json_data['name']])
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
    try:
        with connection.cursor() as cursor:
            try:
                # cart_products 테이블에서 'lines'와 'districts' 가져오기
                cursor.execute('SELECT `lines`, districts FROM cart_products WHERE custom_name = %s', [custom_name])
                result = cursor.fetchone()

                if result is None:
                    raise ValueError(f"No data found for custom_name: {custom_name}")

                lines = result[0]
                districts = result[1]

                # 'lines' 리스트 변환 및 첫 글자 추출
                print(lines.split(','))
                line_list = lines.split(',')
                print(line_list)

                # 'districts' 리스트 변환
                district_list = districts.split(',')

                # subway_stations에서 필터링된 데이터 가져오기
                station_query = 'SELECT * FROM subway_stations WHERE `line` IN %s AND `district` IN %s'
                cursor.execute(station_query, [tuple(line_list), tuple(district_list)])
                filtered_stations = cursor.fetchall()

                if not filtered_stations:
                    raise ValueError("No matching stations found for the given criteria.")

            except Exception as e:
                print(f"Error during station query: {e}")
                connection.rollback()
                return [], []

            # subway_edges에서 필터링된 데이터 가져오기
            try:
                station_id_list = [station[0] for station in filtered_stations]
                
                line_list = [line[0] for line in line_list]
                line_list.append('환승')
                edge_query = 'SELECT * FROM subway_edges WHERE `line` IN %s AND (start_id IN %s OR end_id IN %s)'
                cursor.execute(edge_query, [tuple(line_list), tuple(station_id_list), tuple(station_id_list)])
                filtered_edges = cursor.fetchall()

                if not filtered_edges:
                    raise ValueError("No matching edges found for the given criteria.")

            except Exception as e:
                print(f"Error during edge query: {e}")
                connection.rollback()
                return [], []

        # station 데이터 구성
        stations_data = [
            {
                "id": station[0],
                "name": station[1],
                "line": station[2],
                "latitude": station[3],
                "longitude": station[4],
                "district": station[5],
            }
            for station in filtered_stations
        ]

        # edge 데이터 구성
        edges_data = [
            {
                'id': edge[0],
                'start_id': edge[1],
                'end_id': edge[2],
                'cost': edge[3],
                'line': edge[4],
                'type': edge[5],
            }
            for edge in filtered_edges
        ]

        return stations_data, edges_data

    except Exception as e:
        print(f"Database operation failed: {e}")
        return [], []

