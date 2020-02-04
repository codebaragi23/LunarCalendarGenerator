#-*- coding: utf-8 -*-

from PyQt5 import uic
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

from urllib.parse import urlencode, quote_plus, unquote
from urllib.request import urlopen

from vobject import iCalendar
from parse import compile

import sys
import json
import qdarkstyle

mode_build = getattr(sys, 'frozen', False)
def static_vars(**kwargs):
    def decorate(func):
        for k in kwargs:
            setattr(func, k, kwargs[k])
        return func
    return decorate

class GeneratorTh(QThread):
  # signals
  sig_msg = pyqtSignal(str)
  sig_schedule = pyqtSignal(int)
  sig_prog_setmax = pyqtSignal(int)
  sig_prog_update = pyqtSignal(int)

  def __init__(self):
    super().__init__()
    self.mutex = QMutex()

  def __del__(self):
    self.wait()

  def terminate(self):
    self.mutex.unlock()
    super().terminate()

  def prepare(self, window):
    self.fname = window.ofname
    self.requestLun2Sol = window.requestLun2Sol
    self.leap_month = window.leap_cb_2.currentIndex()
    self.schedules = []
    for r in range(1, window.anni_tw.rowCount()):
      self.schedules.append([window.anni_tw.item(r, 0).text(), window.anni_tw.item(r, 1).text(), window.anni_tw.item(r, 2).text(), window.anni_tw.item(r, 3).text()])
    
    today = QDate.currentDate()
    self.sig_prog_setmax.emit((2051-today.year())*(window.anni_tw.rowCount()-1))

  def run(self):
    self.mutex.lock()
    
    sel = 0
    completed = 1
    self.sig_prog_update.emit(completed)

    cal = iCalendar()
    today = QDate.currentDate()
    for schedule in self.schedules:
      sel += 1
      self.sig_schedule.emit(sel)

      form = schedule[3]
      form = form.replace(form[form.find('d'):form.rfind('d')+1], ('%%0%dd'%form.count('d')))
      context = compile('{month}월 {day}일')
        
      lunar = context.parse(schedule[0]);
      ischecked = schedule[2].isdigit()
      if ischecked:
        cycle = int(schedule[2])
        
      desc = ''
      for year in range(today.year(), 2051):
        dates = self.requestLun2Sol(year, int(lunar['month']), int(lunar['day']))[0]
        date = dates[self.leap_month]

        if ischecked:
          desc = form % cycle + ' (-)%d년'%year + schedule[0];
          cycle += 1

        event = cal.add('vevent')
        event.add('summary').value = schedule[1]
        event.add('description').value = desc
        event.add('dtstart').value = date.toPyDate()
        event.add('dtend').value = date.toPyDate()
        event.add('dtstamp').value = QDateTime.currentDateTime().toPyDateTime()

        completed += 1
        self.sig_prog_update.emit(completed)

      with open(self.fname, 'wb') as f:
        f.write(cal.serialize().encode('utf-8'))

    self.sig_msg.emit('complete')
    self.mutex.unlock()


if mode_build:
  from LunarCalendarGenerator_ui import Ui_MainWindow
  form_class = Ui_MainWindow
else:
  form_class = uic.loadUiType("LunarCalendarGenerator.ui")[0]
class LunarCalendarGenerator(QMainWindow, form_class):
  def __init__(self):
    super().__init__()
    self.setupUi(self)
    self.key = unquote('z9Oyd8rBDlJP2wI3OPwHr%2Fs1QGaQK9yU5LnWplD9i2ptkUrFFYporHpY0me5MqDxs0H%2FkPyY3g68r37JwPoQiw%3D%3D')

    today = QDate.currentDate()
    self.solar_date.setDate(today)

    date, infos = self.requestSol2Lun(today.year(), today.month(), today.day())
    if date is not None:
      self.lunar_date.setDate(date)

    self.anni_tw.itemSelectionChanged.connect(lambda: self.remove_btn.setEnabled(len(self.anni_tw.selectedIndexes()) > 0))
    self.ani_cycle_cb.stateChanged.connect(lambda: self.start_cycle_sb.setEnabled(self.ani_cycle_cb.isChecked()))
    
    self.generator_th = GeneratorTh();
    self.generator_th.sig_msg.connect(self.show_msg)
    self.generator_th.sig_schedule.connect(self.anni_tw.selectRow)
    self.generator_th.sig_prog_setmax.connect(self.generate_pb.setMaximum)
    self.generator_th.sig_prog_update.connect(self.generate_pb.setValue)

    self.show()

  def item2info(self, item):
    inc=0
    if item['solLeapyear'] is '윤': inc+=1
    info = ['양력날짜: %s년 %s월 %s일 (%s요일)' % (item['solYear'], item['solMonth'], item['solDay'], item['solWeek']),
            '음력날짜: %s년 %s월 %s일 (%s달)' % (item['lunYear'], item['lunMonth'], item['lunDay'], item['lunLeapmonth']),
            '음력간지: %s년 %s월 %s일' % (item['lunSecha'], item['lunWolgeon'], item['lunIljin']),
            '율리우스적일: 제 %s일' % (item['solJd']),
            '',
            '윤년정보: 양력 %s년은 %s년으로 %d일까지 있으며 2월은 %d일까지 있습니다.' % (item['solYear'], item['solLeapyear'], 365+inc, 28+inc),
            '윤달정보: 음력 %s년 %s월은 %s달로 %d일까지 있습니다.' % (item['lunYear'], item['lunMonth'], item['lunLeapmonth'], item['lunNday']),]
    return info

  def requestSol2Lun(self, year, month, day):
    url = 'http://apis.data.go.kr/B090041/openapi/service/LrsrCldInfoService/getLunCalInfo'
    queryParams = '?' + urlencode({ quote_plus('ServiceKey') : self.key,
                                    quote_plus('solYear') : str(year).zfill(4), quote_plus('solMonth') : str(month).zfill(2),
                                    quote_plus('solDay') : str(day).zfill(2), quote_plus('_type') : 'json' })

    try:
      response = urlopen(url+queryParams).read().decode('utf-8')
      dict = json.loads(response)
      if dict['response']['body']['totalCount'] > 0 :
        item = dict['response']['body']['items']['item'];
        info = self.item2info(item);
        return QDate(int(item['lunYear']), int(item['lunMonth']), int(item['lunDay'])), info
      else :
        return None, 'Error'
    except Exception as e:
      print('Error: ', e)
      self.show_msg('error');
      return None, 'Error'

  def requestLun2Sol(self, year, month, day):
    url = 'http://apis.data.go.kr/B090041/openapi/service/LrsrCldInfoService/getSolCalInfo'
    queryParams = '?' + urlencode({ quote_plus('ServiceKey') : self.key,
                                    quote_plus('lunYear') : str(year).zfill(4), quote_plus('lunMonth') : str(month).zfill(2),
                                    quote_plus('lunDay') : str(day).zfill(2), quote_plus('_type') : 'json' })
    
    try:
      response = urlopen(url+queryParams).read().decode('utf-8')
      dict = json.loads(response)
      if dict['response']['body']['totalCount'] == 1 :
        item = dict['response']['body']['items']['item'];
        info = self.item2info(item);
        return [QDate(int(item['solYear']), int(item['solMonth']), int(item['solDay']))], [info]
      elif dict['response']['body']['totalCount'] == 2 :
        items = dict['response']['body']['items']['item'];
        dates = []
        infos = []

        item = items[0]
        info = self.item2info(item);
        info.insert(0, '▶ 평달 정보')
        dates.append(QDate(int(item['solYear']), int(item['solMonth']), int(item['solDay'])));
        infos.append(info)

        item = items[1]
        info = self.item2info(item);
        info.insert(0, '▶ 윤달 정보')
        dates.append(QDate(int(item['solYear']), int(item['solMonth']), int(item['solDay'])));
        infos.append(info)
        return dates, infos
      else :
        return None, 'Error'
    except Exception as e:
      print('Error: ', e)
      self.show_msg(1);
      return None, 'Error'

  @pyqtSlot()
  def sol2lun(self):
    date = self.solar_date.date()
    date, info = self.requestSol2Lun(date.year(), date.month(), date.day())
    if date is not None:
      self.lunar_date.setDate(date)
      self.explain_tb.clear()
      for str in info:
        self.explain_tb.append(str)

  @pyqtSlot()
  def lun2sol(self):
    date = self.lunar_date.date()
    dates, infos = self.requestLun2Sol(date.year(), date.month(), date.day())
    if dates is not None:
      sel = 0
      self.infos = infos.copy()
      if self.leap_cb.currentIndex() < 2:
        sel = self.leap_cb.currentIndex()
        info = infos[sel]
      else:
        info = infos[0].copy()
        info.append('')
        info.extend(infos[1])

      date = dates[sel]
      self.solar_date.setDate(date)
      self.explain_tb.clear()
      for str in info:
        self.explain_tb.append(str)

  @pyqtSlot(int)
  def check_leap(self, sel):
    if len(self.infos) > 1 :
      if self.leap_cb.currentIndex() < 2:
        sel = self.leap_cb.currentIndex()
        info = self.infos[sel]
      else:
        info = self.infos[0].copy()
        info.append('')
        info.extend(self.infos[1])

      self.explain_tb.clear()
      for str in info:
        self.explain_tb.append(str)

  @pyqtSlot()
  def add_anni(self):
    date = self.anni_date.date().toString('MM월 dd일')
    anni = self.anni_edit.text()

    start = ''
    if self.ani_cycle_cb.isChecked():
      start = self.start_cycle_sb.text();

    pos = self.anni_tw.rowCount()
    self.anni_tw.insertRow(pos)
    self.anni_tw.setItem(pos, 0, QTableWidgetItem(date))
    self.anni_tw.setItem(pos, 1, QTableWidgetItem(anni))
    self.anni_tw.setItem(pos, 2, QTableWidgetItem(start))

  @pyqtSlot()
  def remove_anni(self):
    self.anni_tw.removeRow(self.anni_tw.currentRow())

  @pyqtSlot(str)
  def show_msg(self, type):
    msg = QMessageBox()
    if type == 'error':
      msg.critical(self, '오류', '정보를 받아올 수 없습니다.')
    elif type == 'complete':
      msg.about(self,'완료','생성이 완료되었습니다.')

  @pyqtSlot()
  def generate(self) :
    fname = QFileDialog.getSaveFileName(None, 'Save', '', '*.ics')[0];
    if len(fname)<0: return

    self.ofname = fname
    if self.generator_th.isRunning():
      self.generator_th.terminate()
    self.generator_th.wait()
    self.generator_th.prepare(self)
    self.generator_th.start()


if __name__ == '__main__':
  app = QApplication(sys.argv)
  window = LunarCalendarGenerator()
  sys.exit(app.exec_())