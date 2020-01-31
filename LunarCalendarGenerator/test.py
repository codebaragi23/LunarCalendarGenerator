#-*- coding: utf-8 -*-

from urllib.parse import urlencode, quote_plus, unquote
from urllib.request import urlopen
import json

key = unquote('z9Oyd8rBDlJP2wI3OPwHr%2Fs1QGaQK9yU5LnWplD9i2ptkUrFFYporHpY0me5MqDxs0H%2FkPyY3g68r37JwPoQiw%3D%3D')
url = 'http://apis.data.go.kr/B090041/openapi/service/LrsrCldInfoService/getSolCalInfo'
queryParams = '?' + urlencode({ quote_plus('ServiceKey') : key, quote_plus('lunYear') : '2020', quote_plus('lunMonth') : '08', quote_plus('lunDay') : '10', quote_plus('_type') : 'json' })

response = urlopen(url + queryParams).read().decode('utf-8')
print(response)

dict = json.loads(response)
item = dict['response']['body']['items']['item'];
print(item['solDay'])
print(item['solMonth'])
