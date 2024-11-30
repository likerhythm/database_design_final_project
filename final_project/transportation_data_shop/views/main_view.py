from django.shortcuts import render


def main(request):
  name = request.session.get('name')
  return render(request, 'main.html', {'name': name})