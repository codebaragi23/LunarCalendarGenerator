#-*- coding: utf-8 -*-
import sys

syn = '10'
if syn.isdigit():
  s = int(syn)
  print(s)
sys.exit(0)


import vobject
from datetime import datetime, date
from PyQt5.QtCore import *
 
cal = vobject.iCalendar()
event = cal.add('vevent')
event.add('summary').value = u'이벤트 하나'
event.add('description').value = u'모두 참석해주세요...'
event.add('dtstart').value = date(2020, 2, 1)
event.add('dtend').value = date(2020, 2, 2)
event.add('dtstamp').value = QDateTime.currentDateTime().toPyDateTime()

event = cal.add('vevent')
event.add('summary').value = u'이벤트 둘'
event.add('description').value = u'모두 참석해주세요...'
event.add('dtstart').value = date(2020, 2, 2)
event.add('dtend').value = date(2020, 2, 3)
event.add('dtstamp').value = QDateTime.currentDateTime().toPyDateTime()

open('example2.ics', 'wb').write(cal.serialize().encode())

sys.exit(0)

from parse import compile

item = ['01월 02일', '생신', '60', 'dd세']
form = item[0]
synt = compile('{month}월 {day}일')
date = synt.parse(form)
print(date['month'])
print(date['day'])

form = item[3]
form = form.replace(form[form.find('d'):form.rfind('d')+1], ('%%0%d'%form.count('d')))
print(form)
sys.exit(0)


from urllib.parse import urlencode, quote_plus, unquote
from urllib.request import urlopen
import json

key = unquote('z9Oyd8rBDlJP2wI3OPwHr%2Fs1QGaQK9yU5LnWplD9i2ptkUrFFYporHpY0me5MqDxs0H%2FkPyY3g68r37JwPoQiw%3D%3D')
year = 2020
month = 1
day = 31

url = 'http://apis.data.go.kr/B090041/openapi/service/LrsrCldInfoService/getSolCalInfo'
queryParams = '?' + urlencode({ quote_plus('ServiceKey') : key, quote_plus('lunYear') : str(year).zfill(4), quote_plus('lunMonth') : str(month).zfill(2), quote_plus('lunDay') : str(day).zfill(2), quote_plus('_type') : 'json' })

response = urlopen(url + queryParams).read().decode('utf-8')
print(response)

dict = json.loads(response)
if dict['response']['body']['totalCount'] > 0 :
  item = dict['response']['body']['items']['item'];
  print(item['solDay'])
  print(item['solMonth'])
else :
  print('Cannt find')




url = 'http://apis.data.go.kr/B090041/openapi/service/LrsrCldInfoService/getLunCalInfo'
queryParams = '?' + urlencode({ quote_plus('ServiceKey') : key, quote_plus('solYear') : str(year).zfill(4), quote_plus('solMonth') : str(month).zfill(2), quote_plus('solDay') : str(day).zfill(2), quote_plus('_type') : 'json' })

response = urlopen(url + queryParams).read().decode('utf-8')
print(response)

dict = json.loads(response)
item = dict['response']['body']['items']['item'];
print(item['lunDay'])
print(item['lunMonth'])