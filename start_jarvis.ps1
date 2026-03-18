Start-Process "ollama" -ArgumentList "serve" -WindowStyle Hidden
Start-Sleep -Seconds 3
& "C:\Users\Leharin\AppData\Local\Python\pythoncore-3.14-64\python.exe" "E:\jarvis-claw\main.py"