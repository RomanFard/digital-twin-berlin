Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "C:\Users\Roman\Documents\code\api"
WshShell.Run "cmd /c ""C:\Program Files\QGIS 4.2.1\apps\Python312\python.exe"" -m uvicorn main:app --host 0.0.0.0 --port 8001", 0, False
WScript.Sleep 5000
WshShell.Run "http://127.0.0.1:8001/dashboard"