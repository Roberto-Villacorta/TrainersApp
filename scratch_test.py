import tkinter as tk
import threading
import time

def worker(root):
    time.sleep(1)
    print("Worker trying to call after...")
    try:
        root.after(0, lambda: print("After executed!"))
    except Exception as e:
        print("Error:", repr(e))
    print("Worker done.")

root = tk.Tk()
threading.Thread(target=worker, args=(root,), daemon=True).start()
root.mainloop()
