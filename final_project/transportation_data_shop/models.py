from django.db import models

class SubwayEdge(models.Model):
  start_id = models.IntegerField()
  end_id = models.IntegerField()
  cost = models.FloatField(null=True, blank=True)  # NULL 값을 허용
  line = models.CharField(max_length=20)
  type = models.CharField(max_length=20)

  class Meta:
    db_table = 'subway_edges'  # 데이터베이스 테이블 이름 명시

class SubwayStation(models.Model):
  name = models.CharField(max_length=20)
  line = models.CharField(max_length=20)
  latitude = models.FloatField()
  longitude = models.FloatField()
  district = models.CharField(max_length=20)

  class Meta:
    db_table = 'subway_stations'

class User(models.Model):
  name = models.CharField(max_length=20)
  login_id = models.CharField(max_length=20)
  password = models.CharField(max_length=20)
  cash = models.IntegerField()

  class Meta:
    db_table = "custom_users"

class Data(models.Model):
  name = models.CharField(max_length=20)
  value = models.JSONField()
  user_id = models.IntegerField()

  class Meta:
    db_table = "datas"

class Cart(models.Model):
  user_id = models.IntegerField()

  class Meta:
    db_table = "carts"

class CartProduct(models.Model):
  cart_id = models.IntegerField()
  lines = models.JSONField()
  district = models.JSONField()
  cost = models.IntegerField()

  class Meta:
    db_table = "cart_products"
