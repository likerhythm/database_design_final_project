import json
from django.db import connection
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.views import View
from ..models import Cart, SubwayStation
from ..models import SubwayEdge
import folium

link_color_mapper = {
  '1': '#0052A4',
  '2': '#00A84D',
  '3': '#EF7C1C',
  '4': '#00A5DE',
  '5': '#996CAC	',
  '6': '#CD7C2F',
  '7': '#747F00',
  '8': '#E6186C',
  '9': '#BB8336',
  '환승': '#FFFFFF',
  '경': '#0052A4',
  '중': '#0052A4',
}

class SubwayView(View):

  def get(self, request):
    name = request.session.get('name')
    print(f'name: {name}')
    return render(request, 'transportation_data_shop.html', {'name': name})
  
  def post(self, request):
    lines = request.POST.getlist('line')
    print(f'lines: {lines}')
    parsed_lines = [item for line in lines for item in line.split(',')]
    districts = request.POST.getlist('district')
    print(f'districts: {districts}')

    stations = SubwayStation.objects.filter(line__in=parsed_lines, district__in=districts)
    all_links = SubwayEdge.objects.all()
    station_list = list(stations)
    all_link_list = list(all_links)
    
    map = folium.Map(location=[37.53427, 126.984750],
                      width=750, 
                      height=500,
                      zoom_start=12)

    for station in station_list:
      name = station.name
      latitude = station.latitude
      longitude = station.longitude
      color = link_color_mapper[station.line[0]]
      folium.Circle(radius=40, location=[latitude, longitude], tooltip=name, color=color).add_to(map)
    
    station_ids = [station.id for station in station_list]
    link_datas = []
    for link in all_link_list:
      start_id = link.start_id
      end_id = link.end_id
      line_name = link.line
      if start_id in station_ids and end_id in station_ids:
        link_datas.append([start_id, end_id, line_name])
    
    for start_id, end_id, line_name in link_datas:
      start_position = [
        next((station.latitude for station in station_list if station.id == start_id), None),
        next((station.longitude for station in station_list if station.id == start_id), None)
      ]

      end_position = [
        next((station.latitude for station in station_list if station.id == end_id), None),
        next((station.longitude for station in station_list if station.id == end_id), None)
      ]

      link_color = link_color_mapper[line_name]
      folium.PolyLine(locations=[start_position, end_position], color=link_color).add_to(map)

    displayed_lines = [line for line in parsed_lines if str.isdigit(line[0])]
    name = request.session.get('name')
    context = {
      'map': map._repr_html_(),
      'choosed_lines': ','.join(displayed_lines),
      'choosed_districts': ','.join(districts),
      'name': name
    }

    return render(request, 'transportation_data_shop.html', context)

def add_to_cart(request):
  if request.method == 'POST':
    decoded_body = request.body.decode('utf-8')  # 바이트 문자열을 UTF-8로 디코딩
    print("Decoded Body:", decoded_body)  # 디코딩된 문자열 확인
    try:
      # JSON 데이터 파싱
      data = json.loads(request.body)
      choosed_lines = data.get('choosed_lines', '')
      choosed_districts = data.get('choosed_districts', '')
      custom_name = data.get('alias', '')
      print('choosed_lines:', choosed_lines)
      print('choosed_districts:', choosed_districts)
      user_id = request.session.get('user_id')

      with connection.cursor() as cursor:
              # Check if custom_name already exists for the user's cart
              cursor.execute(
                  """
                  SELECT 1 
                  FROM cart_products 
                  WHERE custom_name = %s 
                    AND cart_id = (SELECT id FROM carts WHERE user_id = %s)
                  """, 
                  [custom_name, user_id]
              )
              existing_name = cursor.fetchone()

      if existing_name:
          print(f'중복된 custom_name: {custom_name}')
          return JsonResponse(
              {'error': '별칭이 중복되었습니다. 다른 이름을 입력하세요.', 'details': custom_name}, 
              status=400
          )

      print('user_id:', user_id)
      with connection.cursor() as cursor:
        cursor.execute("SELECT id FROM carts WHERE user_id = %s", [user_id])
        result = cursor.fetchone()
        cart_id = result[0]  # name 값 추출
        print('cart_id:', cart_id)
      # 데이터베이스에 저장
      
      cost = calc_cost(choosed_lines, choosed_districts)
      print('cost:', cost)
      with connection.cursor() as cursor:
        cursor.execute("INSERT INTO cart_products (cart_id, `lines`, districts, cost, custom_name) VALUES (%s, %s, %s, %s, %s)",
                      [cart_id, 
                        choosed_lines,  # JSON 배열로 저장
                        choosed_districts,  # JSON 배열로 저장
                        cost,
                        custom_name])
      print('저장 완료')
      return JsonResponse({'message': '장바구니에 성공적으로 추가되었습니다!', 'user_id': user_id}, status=200)
    except Exception as e:
        return JsonResponse({'error': '요청 처리 중 에러가 발생했습니다.', 'details': str(e)}, status=400)

  return JsonResponse({'error': '잘못된 요청입니다.'}, status=400)

def calc_cost(lines, districts):
  return len(lines.split(',')) * 1000 + len(districts.split(',')) * 1000
