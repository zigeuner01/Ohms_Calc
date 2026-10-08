#!/usr/bin/env python3
# Ohm's Law Calculator with series, parallel support + optional power calculations and Tkinter GUI
# GitHub Copilot style concise CLI with explanations

import sys
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

def input_float(prompt):
    while True:
        try:
            return float(input(prompt).strip())
        except ValueError:
            print("Please enter a valid number.")

def input_positive_float(prompt):
    while True:
        v = input_float(prompt)
        if v <= 0:
            print("Value must be > 0.")
        else:
            return v

def ohms_from_two(known):
    # known is dict with possible keys 'V','I','R'
    keys = [k for k in ('V', 'I', 'R') if k in known and known[k] is not None]
    if len(keys) < 2:
        raise ValueError("Need at least two known quantities among V, I and R.")
    if 'V' not in keys:
        known['V'] = known['I'] * known['R']
    elif 'I' not in keys:
        known['I'] = known['V'] / known['R']
    elif 'R' not in keys:
        known['R'] = known['V'] / known['I']
    return known

def series_total(resistors):
    total = sum(resistors)
    return total

def parallel_total(resistors):
    inv_sum = sum(1.0 / r for r in resistors)
    total = 1.0 / inv_sum
    return total

def compute_power_from_VI(V=None, I=None, R=None):
    # returns P in watts from given available values
    if V is not None and I is not None:
        return V * I
    if I is not None and R is not None:
        return (I ** 2) * R
    if V is not None and R is not None:
        return (V ** 2) / R
    return None

def ask_voltage_current_distribution_cli(total_R, resistors, connection_type, V=None, I=None, want_power=False):
    # CLI helper: compute missing total and per-branch values, print results
    if V is None and I is None:
        print("No total V or I provided; cannot compute line voltages/currents.")
        return
    if V is None and I is not None:
        V = I * total_R
        print(f"Derived total voltage V = I_total * R_eq = {I} * {total_R} = {V} V")
    if I is None and V is not None:
        I = V / total_R
        print(f"Derived total current I = V_total / R_eq = {V} / {total_R} = {I} A")
    print(f"Total: V={V} V, I={I} A, R_eq={total_R} Ω")
    results = []
    if connection_type == 'series':
        for idx, r in enumerate(resistors, 1):
            v_drop = I * r
            p = compute_power_from_VI(V=v_drop, I=I, R=r) if want_power else None
            results.append((f"R{idx}", r, I, v_drop, p))
    else:  # parallel
        for idx, r in enumerate(resistors, 1):
            v = V
            i_branch = v / r
            p = compute_power_from_VI(V=v, I=i_branch, R=r) if want_power else None
            results.append((f"R{idx}", r, i_branch, v, p))
    for item in results:
        if connection_type == 'series':
            name, r, i_branch, v_drop, p = item
            if want_power:
                print(f"{name} {r}Ω: I={i_branch:.6g}A, V_drop={v_drop:.6g}V, P={p:.6g}W")
            else:
                print(f"{name} {r}Ω: I={i_branch:.6g}A, V_drop={v_drop:.6g}V")
        else:
            name, r, i_branch, v, p = item
            if want_power:
                print(f"{name} {r}Ω: V={v:.6g}V, I_branch={i_branch:.6g}A, P={p:.6g}W")
            else:
                print(f"{name} {r}Ω: V={v:.6g}V, I_branch={i_branch:.6g}A")

def parse_resistors(text):
    # Accept comma/space separated values, ignore empty tokens
    tokens = [t.strip() for t in text.replace(',', ' ').split()]
    resistors = []
    for t in tokens:
        try:
            v = float(t)
            if v <= 0:
                raise ValueError
            resistors.append(v)
        except ValueError:
            raise ValueError(f"Invalid resistor value: '{t}'")
    if not resistors:
        raise ValueError("No resistor values provided.")
    return resistors

# --- Tkinter GUI ---

class OhmGui(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Ohm's Law Calculator")
        self.geometry("760x520")
        self._build_ui()

    def _build_ui(self):
        main = ttk.Frame(self, padding=8)
        main.pack(fill=tk.BOTH, expand=True)

        # Top: input frame
        inp = ttk.LabelFrame(main, text="Inputs", padding=8)
        inp.pack(fill=tk.X, padx=4, pady=4)

        row = 0
        ttk.Label(inp, text="Voltage V (leave blank if unknown)").grid(column=0, row=row, sticky=tk.W)
        self.v_entry = ttk.Entry(inp, width=16)
        self.v_entry.grid(column=1, row=row, sticky=tk.W, padx=4)

        ttk.Label(inp, text="Current I (leave blank if unknown)").grid(column=2, row=row, sticky=tk.W)
        self.i_entry = ttk.Entry(inp, width=16)
        self.i_entry.grid(column=3, row=row, sticky=tk.W, padx=4)

        ttk.Label(inp, text="Resistance R (single resistor; optional)").grid(column=4, row=row, sticky=tk.W)
        self.r_entry = ttk.Entry(inp, width=16)
        self.r_entry.grid(column=5, row=row, sticky=tk.W, padx=4)

        row += 1
        ttk.Label(inp, text="Resistors list (comma or space separated)").grid(column=0, row=row, sticky=tk.W, pady=6)
        self.resistors_entry = ttk.Entry(inp, width=60)
        self.resistors_entry.grid(column=1, row=row, columnspan=3, sticky=tk.W, padx=4)

        ttk.Label(inp, text="Connection").grid(column=4, row=row, sticky=tk.W)
        self.conn_var = tk.StringVar(value='series')
        ttk.Radiobutton(inp, text="Series", variable=self.conn_var, value='series').grid(column=5, row=row, sticky=tk.W)
        ttk.Radiobutton(inp, text="Parallel", variable=self.conn_var, value='parallel').grid(column=5, row=row, sticky=tk.E)

        row += 1
        self.power_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(inp, text="Calculate power (per element & total)", variable=self.power_var).grid(column=0, row=row, sticky=tk.W, pady=6)

        ttk.Button(inp, text="Compute", command=self.on_compute).grid(column=5, row=row, sticky=tk.E)

        # Middle: output frame
        out = ttk.LabelFrame(main, text="Results", padding=8)
        out.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        self.out_text = scrolledtext.ScrolledText(out, wrap=tk.WORD, height=20)
        self.out_text.pack(fill=tk.BOTH, expand=True)

        # Bottom: small help
        helpf = ttk.Frame(main)
        helpf.pack(fill=tk.X, padx=4, pady=2)
        ttk.Label(helpf, text="Enter at least two of V, I, R for single resistor calc; or provide resistor list for series/parallel").pack(side=tk.LEFT)

    def on_compute(self):
        self.out_text.delete('1.0', tk.END)
        try:
            V = self._parse_optional_float(self.v_entry.get())
            I = self._parse_optional_float(self.i_entry.get())
            R = self._parse_optional_float(self.r_entry.get())
            resistors_text = self.resistors_entry.get().strip()
            results = []
            # Single resistor ohm's-law if R provided or if two of V/I/R provided
            if any(x is not None for x in (V, I, R)):
                known = {'V': V, 'I': I, 'R': R}
                known = {k: v for k, v in known.items() if v is not None}
                if len(known) >= 2:
                    solved = ohms_from_two(dict(known))  # returns dict with computed fields
                    results.append("Single-resistor calculation:")
                    results.append(f"  V = {solved.get('V', 'N/A')} V")
                    results.append(f"  I = {solved.get('I', 'N/A')} A")
                    results.append(f"  R = {solved.get('R', 'N/A')} Ω")
                    if self.power_var.get():
                        p = compute_power_from_VI(V=solved.get('V'), I=solved.get('I'), R=solved.get('R'))
                        results.append(f"  Power P = {p} W")
                    results.append("")
                elif resistors_text == "":
                    results.append("Not enough info for single-resistor calculation (need 2 of V,I,R).")
            # If resistor list provided, compute series/parallel totals and distributions
            if resistors_text:
                resistors = parse_resistors(resistors_text)
                conn = self.conn_var.get()
                if conn == 'series':
                    R_eq = series_total(resistors)
                else:
                    R_eq = parallel_total(resistors)
                results.append(f"{conn.capitalize()} connection equivalent resistance: R_eq = {R_eq:.6g} Ω")
                # derive missing totals
                Vtot = V
                Itot = I
                if Vtot is None and Itot is None:
                    results.append("No total V or I provided for distribution; provide V or I to compute branch values.")
                else:
                    if Vtot is None and Itot is not None:
                        Vtot = Itot * R_eq
                        results.append(f"Derived total V = I_total * R_eq = {Itot} * {R_eq} = {Vtot} V")
                    if Itot is None and Vtot is not None:
                        Itot = Vtot / R_eq
                        results.append(f"Derived total I = V_total / R_eq = {Vtot} / {R_eq} = {Itot} A")
                    results.append(f"Total: V={Vtot} V, I={Itot} A")
                    if conn == 'series':
                        results.append("Per-element (series):")
                        for idx, r in enumerate(resistors, 1):
                            v_drop = Itot * r
                            p = compute_power_from_VI(V=v_drop, I=Itot, R=r) if self.power_var.get() else None
                            if p is not None:
                                results.append(f"  R{idx}={r}Ω: I={Itot:.6g}A, V_drop={v_drop:.6g}V, P={p:.6g}W")
                            else:
                                results.append(f"  R{idx}={r}Ω: I={Itot:.6g}A, V_drop={v_drop:.6g}V")
                    else:
                        results.append("Per-branch (parallel):")
                        for idx, r in enumerate(resistors, 1):
                            v = Vtot
                            i_branch = v / r
                            p = compute_power_from_VI(V=v, I=i_branch, R=r) if self.power_var.get() else None
                            if p is not None:
                                results.append(f"  R{idx}={r}Ω: V={v:.6g}V, I_branch={i_branch:.6g}A, P={p:.6g}W")
                            else:
                                results.append(f"  R{idx}={r}Ω: V={v:.6g}V, I_branch={i_branch:.6g}A")
                    # total power if requested
                    if self.power_var.get():
                        p_total = compute_power_from_VI(V=Vtot, I=Itot, R=R_eq)
                        if p_total is None:
                            # fallback compute as sum of per-element powers
                            if conn == 'series':
                                p_total = sum(compute_power_from_VI(V=Itot*r, I=Itot, R=r) for r in resistors)
                            else:
                                p_total = sum(compute_power_from_VI(V=Vtot, I=Vtot/r, R=r) for r in resistors)
                        results.append(f"Total power P_total = {p_total:.6g} W")
                results.append("")
            # show results
            if not results:
                results.append("No calculations performed. Provide inputs or resistor list.")
            self.out_text.insert(tk.END, "\n".join(results))
        except Exception as ex:
            messagebox.showerror("Error", str(ex))

    def _parse_optional_float(self, s):
        s = s.strip()
        if s == "":
            return None
        try:
            return float(s)
        except ValueError:
            raise ValueError(f"Invalid numeric value: '{s}'")

# --- CLI main for backward compatibility ---

def cli_menu():
    print("Ohm's Law CLI - options:")
    print("1) Single resistor: provide two of V, I, R to compute the third")
    print("2) Series/Parallel resistors: provide resistor list and total V or I to compute distribution")
    print("3) Launch GUI")
    print("q) Quit")
    while True:
        choice = input("Select option: ").strip().lower()
        if choice in ('q', 'quit', 'exit'):
            return
        if choice == '1':
            known = {}
            s = input("Enter Voltage V (blank if unknown): ").strip()
            if s != "":
                known['V'] = float(s)
            s = input("Enter Current I (blank if unknown): ").strip()
            if s != "":
                known['I'] = float(s)
            s = input("Enter Resistance R (blank if unknown): ").strip()
            if s != "":
                known['R'] = float(s)
            try:
                solved = ohms_from_two(dict(known))
                print("Result:", solved)
                do_power = input("Compute power? (y/n): ").strip().lower() == 'y'
                if do_power:
                    p = compute_power_from_VI(V=solved.get('V'), I=solved.get('I'), R=solved.get('R'))
                    print(f"Power P = {p} W")
            except Exception as e:
                print("Error:", e)
        elif choice == '2':
            text = input("Enter resistors (comma or space separated): ")
            try:
                resistors = parse_resistors(text)
            except Exception as e:
                print("Error:", e)
                continue
            conn = input("Connection (series/parallel): ").strip().lower()
            if conn not in ('series', 'parallel'):
                print("Invalid connection.")
                continue
            have_v = input("Have total V? (y/n): ").strip().lower() == 'y'
            V = None
            I = None
            if have_v:
                V = input_float("Enter total V: ")
            have_i = input("Have total I? (y/n): ").strip().lower() == 'y'
            if have_i:
                I = input_float("Enter total I: ")
            want_power = input("Compute power? (y/n): ").strip().lower() == 'y'
            if conn == 'series':
                R_eq = series_total(resistors)
            else:
                R_eq = parallel_total(resistors)
            print(f"R_eq = {R_eq} Ω")
            ask_voltage_current_distribution_cli(R_eq, resistors, conn, V=V, I=I, want_power=want_power)
        elif choice == '3':
            launch_gui()
            return
        else:
            print("Unknown option.")

def launch_gui():
    app = OhmGui()
    app.mainloop()

if __name__ == "__main__":
    # default behavior: if '-g' passed launch GUI, else show menu which allows launching GUI
    if len(sys.argv) > 1 and sys.argv[1] in ('-g', '--gui'):
        launch_gui()
    else:
        # run CLI menu; user can choose to launch GUI from there
        try:
            cli_menu()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
