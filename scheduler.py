import schedule
from mock_simple import run
import time

print('[INFO] - Scheduler iniciando')
schedule.every().day.at("03:00").do(run)
print('[INFO] - Tarefa agendada')

while True:
    schedule.run_pending()
    try:
        time.sleep(600)  # Verificar a cada 10 minutos
    except KeyboardInterrupt:
        print("[EXIT] - Scheduler interrompido pelo usuário.")
        break
