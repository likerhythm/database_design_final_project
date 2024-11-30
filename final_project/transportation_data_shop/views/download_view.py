from django.http import FileResponse, Http404, JsonResponse
import os

def download_file(request, file_name):
    try:
        # 세션에서 사용자 ID 가져오기
        user_id = request.session.get('user_id')
        if not user_id:
            return JsonResponse({'error': '로그인이 필요합니다.'}, status=403)

        # 파일 경로 생성 (files/<user_id>/<file_name>)
        file_name = file_name + '.json'
        file_path = os.path.join("files", str(user_id), file_name)
        mime_type = 'application/json'
        print(f'file_path: {file_path}')
        # 파일 존재 여부 확인
        if not os.path.exists(file_path):
            raise Http404("파일이 존재하지 않습니다.")

        # 파일 응답 반환
        return FileResponse(
              open(file_path, "rb"),
              as_attachment=True,
              filename=file_name,
              content_type="application/json"
              )

    except Http404 as e:
        # 파일이 없는 경우 404 반환
        return JsonResponse({'error': str(e)}, status=404)

    except Exception as e:
        # 기타 예외 처리
        return JsonResponse({'error': '파일 다운로드 중 오류가 발생했습니다.', 'details': str(e)}, status=500)
