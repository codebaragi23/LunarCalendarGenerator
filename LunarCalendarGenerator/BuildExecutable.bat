pyrcc5 LunarCalendarGenerator.qrc -o LunarCalendarGenerator_rc.py
pyuic5 LunarCalendarGenerator.ui -o LunarCalendarGenerator_ui.py
pyinstaller --onefile --windowed LunarCalendarGenerator.py