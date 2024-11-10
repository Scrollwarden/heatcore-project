import os
import multiprocessing
import time

# Fonction exécutée par chaque processus
def worker():
    print(f"Processus enfant (PID: {os.getpid()}) démarré")
    time.sleep(2)  # Simule une tâche en attente
    print(f"Processus enfant (PID: {os.getpid()}) terminé")

if __name__ == '__main__':
    # PID du processus principal
    print(f"Processus principal (PID: {os.getpid()}) démarré")

    # Création de plusieurs processus enfants
    processes : list[multiprocessing.Process] = []
    for i in range(5):  # Création de 5 processus
        p = multiprocessing.Process(target=worker)
        processes.append(p)
        p.start()

    # Attente de la fin de tous les processus enfants
    for p in processes:
        p.join()

    print(f"Processus principal (PID: {os.getpid()}) terminé")
