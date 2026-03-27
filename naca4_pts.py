
import math
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import numpy as np

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


def naca4_points_base(code: str, n_side: int = 100, chord: float = 1.0):
    """
    Genera un profilo NACA 4 cifre con trailing edge geometrico chiuso.
    Output base:
    - ordine: estradosso TE -> LE, poi intradosso LE -> TE
    - primo e ultimo punto coincidono sul trailing edge
    - 3 colonne finali previste dal writer .pts: x, y, z(=0)

    n_side=100 -> 201 punti totali
    """
    code = code.strip()
    if len(code) != 4 or not code.isdigit():
        raise ValueError("Il codice NACA deve avere 4 cifre, ad esempio 2412 o 0012.")

    m = int(code[0]) / 100.0
    p = int(code[1]) / 10.0
    t = int(code[2:4]) / 100.0

    beta = np.linspace(0.0, math.pi, n_side + 1)
    x = 0.5 * (1.0 - np.cos(beta))  # 0 -> 1

    # Trailing edge sempre chiuso
    a4 = -0.1036

    yt = 5.0 * t * (
        0.2969 * np.sqrt(np.maximum(x, 0.0))
        - 0.1260 * x
        - 0.3516 * x**2
        + 0.2843 * x**3
        + a4 * x**4
    )

    yc = np.zeros_like(x)
    dyc_dx = np.zeros_like(x)

    if m > 0 and p > 0:
        mask1 = x < p
        mask2 = ~mask1

        yc[mask1] = (m / p**2) * (2 * p * x[mask1] - x[mask1] ** 2)
        dyc_dx[mask1] = (2 * m / p**2) * (p - x[mask1])

        yc[mask2] = (m / (1 - p) ** 2) * ((1 - 2 * p) + 2 * p * x[mask2] - x[mask2] ** 2)
        dyc_dx[mask2] = (2 * m / (1 - p) ** 2) * (p - x[mask2])

    theta = np.arctan(dyc_dx)

    xu = x - yt * np.sin(theta)
    yu = yc + yt * np.cos(theta)

    xl = x + yt * np.sin(theta)
    yl = yc - yt * np.cos(theta)

    xu *= chord
    yu *= chord
    xl *= chord
    yl *= chord

    upper_x = xu[::-1]
    upper_y = yu[::-1]

    lower_x = xl[1:]
    lower_y = yl[1:]

    x_all = np.concatenate([upper_x, lower_x])
    y_all = np.concatenate([upper_y, lower_y])

    # Chiusura profilo sempre: ultimo punto uguale al primo
    if not (np.isclose(x_all[0], x_all[-1]) and np.isclose(y_all[0], y_all[-1])):
        x_all = np.append(x_all, x_all[0])
        y_all = np.append(y_all, y_all[0])

    z_all = np.zeros_like(x_all)
    return x_all, y_all, z_all


def transform_points(x, y, angle_deg=0.0, mirror_x=False, mirror_y=False):
    x = np.array(x, dtype=float)
    y = np.array(y, dtype=float)

    # specchio rispetto asse X: y -> -y
    if mirror_x:
        y = -y

    # specchio rispetto asse Y: x -> -x
    if mirror_y:
        x = -x

    if angle_deg:
        ang = math.radians(angle_deg)
        c = math.cos(ang)
        s = math.sin(ang)
        xr = x * c - y * s
        yr = x * s + y * c
        x, y = xr, yr

    return x, y


def format_number(value: float, decimals: int = 6) -> str:
    if abs(value) < 0.5 * 10**(-decimals):
        return "0"
    if abs(value - round(value)) < 0.5 * 10**(-decimals):
        return str(int(round(value)))
    return f"{value:.{decimals}f}"


def build_pts_text(code: str, n_side: int, chord: float, angle_deg: float,
                   mirror_x: bool, mirror_y: bool, decimals: int = 6):
    x_all, y_all, z_all = naca4_points_base(code=code, n_side=n_side, chord=chord)
    x_all, y_all = transform_points(
        x_all, y_all, angle_deg=angle_deg, mirror_x=mirror_x, mirror_y=mirror_y
    )

    lines = []
    for x, y, z in zip(x_all, y_all, z_all):
        lines.append(
            f"{format_number(float(x), decimals)}\t"
            f"{format_number(float(y), decimals)}\t"
            f"{format_number(float(z), decimals)}"
        )
    return "\n".join(lines), x_all, y_all, z_all


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Generatore NACA 4 cifre -> .pts compatibile con grafico live")
        self.root.geometry("1220x760")

        self._update_job = None

        main = ttk.Frame(root, padding=10)
        main.pack(fill="both", expand=True)

        left = ttk.Frame(main)
        left.pack(side="left", fill="y", padx=(0, 10))

        right = ttk.Frame(main)
        right.pack(side="left", fill="both", expand=True)

        params = ttk.LabelFrame(left, text="Parametri", padding=10)
        params.pack(fill="x")

        self.code_var = tk.StringVar(value="0030")
        self.chord_var = tk.StringVar(value="1.0")
        self.n_side_var = tk.StringVar(value="100")
        self.angle_var = tk.StringVar(value="0")
        self.decimals_var = tk.StringVar(value="6")
        self.mirror_x_var = tk.BooleanVar(value=False)
        self.mirror_y_var = tk.BooleanVar(value=False)

        row = 0
        ttk.Label(params, text="Profilo NACA").grid(row=row, column=0, sticky="w", pady=4)
        e = ttk.Entry(params, textvariable=self.code_var, width=12)
        e.grid(row=row, column=1, sticky="w", pady=4)
        e.bind("<KeyRelease>", self.schedule_update)

        row += 1
        ttk.Label(params, text="Corda").grid(row=row, column=0, sticky="w", pady=4)
        e = ttk.Entry(params, textvariable=self.chord_var, width=12)
        e.grid(row=row, column=1, sticky="w", pady=4)
        e.bind("<KeyRelease>", self.schedule_update)

        row += 1
        ttk.Label(params, text="Punti per semiprofilo").grid(row=row, column=0, sticky="w", pady=4)
        e = ttk.Entry(params, textvariable=self.n_side_var, width=12)
        e.grid(row=row, column=1, sticky="w", pady=4)
        e.bind("<KeyRelease>", self.schedule_update)

        row += 1
        ttk.Label(params, text="Rotazione (gradi)").grid(row=row, column=0, sticky="w", pady=4)
        e = ttk.Entry(params, textvariable=self.angle_var, width=12)
        e.grid(row=row, column=1, sticky="w", pady=4)
        e.bind("<KeyRelease>", self.schedule_update)

        row += 1
        ttk.Label(params, text="Decimali").grid(row=row, column=0, sticky="w", pady=4)
        e = ttk.Entry(params, textvariable=self.decimals_var, width=12)
        e.grid(row=row, column=1, sticky="w", pady=4)
        e.bind("<KeyRelease>", self.schedule_update)

        row += 1
        ttk.Checkbutton(
            params, text="Specchia su asse X", variable=self.mirror_x_var,
            command=self.update_preview
        ).grid(row=row, column=0, columnspan=2, sticky="w", pady=4)

        row += 1
        ttk.Checkbutton(
            params, text="Specchia su asse Y", variable=self.mirror_y_var,
            command=self.update_preview
        ).grid(row=row, column=0, columnspan=2, sticky="w", pady=4)

        row += 1
        ttk.Separator(params, orient="horizontal").grid(row=row, column=0, columnspan=2, sticky="ew", pady=8)

        row += 1
        ttk.Button(params, text="Aggiorna", command=self.update_preview).grid(row=row, column=0, sticky="ew", pady=4)
        ttk.Button(params, text="Salva .pts", command=self.save_pts).grid(row=row, column=1, sticky="ew", pady=4)

        row += 1
        ttk.Button(params, text="Copia anteprima", command=self.copy_preview).grid(row=row, column=0, columnspan=2, sticky="ew", pady=4)

        note = ttk.LabelFrame(left, text="Formato output", padding=10)
        note.pack(fill="x", pady=(10, 0))
        ttk.Label(
            note,
            text=(
                "- formato .pts: x TAB y TAB z\n"
                "- z sempre = 0\n"
                "- chiusura profilo sempre attiva\n"
                "- trailing edge sempre chiuso\n"
                "- ordine: TE superiore -> LE -> TE inferiore\n"
                "- con 100 punti/semiprofilo ottieni 201 righe"
            ),
            justify="left"
        ).pack(anchor="w")

        graph_frame = ttk.LabelFrame(right, text="Grafico profilo (aggiornamento live)", padding=8)
        graph_frame.pack(fill="both", expand=True)

        self.figure = Figure(figsize=(7, 4.5), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_title("Profilo")
        self.ax.set_xlabel("X")
        self.ax.set_ylabel("Y")
        self.ax.grid(True)
        self.ax.set_aspect("equal", adjustable="box")

        self.canvas = FigureCanvasTkAgg(self.figure, master=graph_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        preview_frame = ttk.LabelFrame(right, text="Anteprima .pts", padding=8)
        preview_frame.pack(fill="both", expand=True, pady=(10, 0))

        self.text = tk.Text(preview_frame, wrap="none", font=("Consolas", 10), height=14)
        self.text.pack(fill="both", expand=True)

        xscroll = ttk.Scrollbar(preview_frame, orient="horizontal", command=self.text.xview)
        xscroll.pack(fill="x")
        yscroll = ttk.Scrollbar(preview_frame, orient="vertical", command=self.text.yview)
        yscroll.place(relx=1.0, rely=0.0, relheight=1.0, anchor="ne")
        self.text.configure(xscrollcommand=xscroll.set, yscrollcommand=yscroll.set)

        self.last_pts_text = ""
        self.last_x = None
        self.last_y = None

        self.update_preview()

    def schedule_update(self, event=None):
        if self._update_job is not None:
            self.root.after_cancel(self._update_job)
        self._update_job = self.root.after(250, self.update_preview)

    def get_values(self):
        code = self.code_var.get().strip()
        chord = float(self.chord_var.get().replace(",", "."))
        n_side = int(self.n_side_var.get())
        angle_deg = float(self.angle_var.get().replace(",", "."))
        decimals = int(self.decimals_var.get())

        if chord <= 0:
            raise ValueError("La corda deve essere maggiore di zero.")
        if n_side < 2:
            raise ValueError("I punti per semiprofilo devono essere almeno 2.")
        if decimals < 0 or decimals > 12:
            raise ValueError("I decimali devono essere compresi tra 0 e 12.")

        return {
            "code": code,
            "chord": chord,
            "n_side": n_side,
            "angle_deg": angle_deg,
            "decimals": decimals,
            "mirror_x": self.mirror_x_var.get(),
            "mirror_y": self.mirror_y_var.get(),
        }

    def update_preview(self):
        self._update_job = None
        try:
            vals = self.get_values()
            pts_text, x, y, _ = build_pts_text(**vals)

            self.last_pts_text = pts_text
            self.last_x = x
            self.last_y = y

            self.text.delete("1.0", "end")
            self.text.insert("1.0", pts_text)

            self.redraw_plot(x, y, vals)
        except Exception as e:
            self.show_plot_error(str(e))

    def redraw_plot(self, x, y, vals):
        self.ax.clear()
        self.ax.plot(x, y, marker=".", markersize=2)
        self.ax.set_title(
            f"NACA {vals['code']} | corda={vals['chord']} | rot={vals['angle_deg']}°"
        )
        self.ax.set_xlabel("X")
        self.ax.set_ylabel("Y")
        self.ax.grid(True)
        self.ax.set_aspect("equal", adjustable="box")

        if len(x) > 0:
            xmin, xmax = float(np.min(x)), float(np.max(x))
            ymin, ymax = float(np.min(y)), float(np.max(y))
            dx = xmax - xmin
            dy = ymax - ymin
            pad_x = max(dx * 0.08, vals["chord"] * 0.02)
            pad_y = max(dy * 0.12, vals["chord"] * 0.02)
            self.ax.set_xlim(xmin - pad_x, xmax + pad_x)
            self.ax.set_ylim(ymin - pad_y, ymax + pad_y)

        self.canvas.draw_idle()

    def show_plot_error(self, msg):
        self.ax.clear()
        self.ax.text(0.5, 0.5, msg, ha="center", va="center", wrap=True)
        self.ax.set_axis_off()
        self.canvas.draw_idle()

    def save_pts(self):
        try:
            vals = self.get_values()
            pts_text, _, _, _ = build_pts_text(**vals)

            default_name = f"NACA{vals['code']}.pts"
            path = filedialog.asksaveasfilename(
                title="Salva file .pts",
                defaultextension=".pts",
                initialfile=default_name,
                filetypes=[("PTS files", "*.pts"), ("Tutti i file", "*.*")]
            )
            if not path:
                return

            with open(path, "w", encoding="utf-8", newline="\n") as f:
                f.write(pts_text)

            messagebox.showinfo("Salvato", f"File salvato correttamente:\n{path}")
        except Exception as e:
            messagebox.showerror("Errore", str(e))

    def copy_preview(self):
        txt = self.text.get("1.0", "end-1c")
        self.root.clipboard_clear()
        self.root.clipboard_append(txt)
        self.root.update()
        messagebox.showinfo("Copiato", "Anteprima copiata negli appunti.")


def main():
    root = tk.Tk()
    try:
        style = ttk.Style()
        if "vista" in style.theme_names():
            style.theme_use("vista")
    except Exception:
        pass
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
