import customtkinter as ctk

app = ctk.CTk()
app.geometry("400x400")

scrollable = ctk.CTkScrollableFrame(app)
scrollable.pack(fill="both", expand=True)

for i in range(100):
    ctk.CTkLabel(scrollable, text=f"Item {i}").pack()

def smooth_scroll(canvas, delta, steps, delay):
    if steps > 0:
        canvas.yview_scroll(int(delta), "units")
        app.after(delay, smooth_scroll, canvas, delta, steps - 1, delay)

def on_mouse(event):
    # En win32 event.delta suele ser +-120
    # En vez de scrollear 1 vez por 1 unidad bruta
    # hacemos pequeños steps? No, .yview_scroll(1, units) es el minimo
    pass

app.after(1000, lambda: print("canvas yscrollincrement es", scrollable._parent_canvas.cget('yscrollincrement')))
app.after(2000, app.destroy)
app.mainloop()
