"""
M-Store Admin - E-commerce Backend
-----------------------------------
Pure Python (Tkinter only, no external chart libraries).

Flow:
    1. App starts at the Auth window (Login / Create Account toggle).
    2. On successful login, the Auth window closes and the Dashboard
       (main admin window) opens.
    3. Logging out from the Dashboard returns to the Auth window.

Accounts are stored locally in admin_users.json (username, salted
password hash, email, created date). No external DB/network needed.
"""

import json
import os
import hashlib
import random
import string
import math
from datetime import datetime, timedelta

import tkinter as tk
from tkinter import *
from flask import Flask, render_template, request, redirect, url_for, session
USERS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "admin_users.json")

app = Flask(__name__)

@app.route("/")
def home():
    return "Hello, Render!"
#if __name__ == '__main__':
    #appBcd.run(debug=True)

# ========================<Zc=============================================
# THEME
# =====================================================================

class Theme:
    SIDEBAR_BG = "#1B2559"
    SIDEBAR_ACTIVE = "#4318FF"
    SIDEBAR_TEXT = "#A3AED0"
    SIDEBAR_TEXT_ACTIVE = "#FFFFFF"
    MAIN_BG = "#F4F7FE"
    CARD_BG = "#FFFFFF"
    TEXT_DARK = "#1B2559"
    TEXT_MUTED = "#A3AED0"
    BORDER = "#E9EDF7"

    PURPLE = "#7B61FF"
    BLUE = "#3F8CFF"
    GREEN = "#2ED47A"
    ORANGE = "#FFA53E"
    RED = "#FF5B5B"

    FONT = "Segoe UI"


# =====================================================================
# USER STORAGE (JSON file, sha256 salted hashes)
# =====================================================================
def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)


def hash_password(password, salt):
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()


def create_user(username, email, password):
    username = username.strip()
    email = email.strip()
    if not username or not email or not password:
        return False, "Please fill in all fields."
    users = load_users()
    if username in users:
        return False, "That username is already taken."
    salt = "".join(random.choices(string.ascii_letters + string.digits, k=16))
    users[username] = {
        "email": email,
        "salt": salt,
        "password_hash": hash_password(password, salt),
        "created": datetime.now().strftime("%b %d, %Y"),
    }
    save_users(users)
    return True, "Account created successfully."


def verify_user(username, password):
    users = load_users()
    record = users.get(username.strip())
    if not record:
        return False, "No account found with that username."
    if hash_password(password, record["salt"]) != record["password_hash"]:
        return False, "Incorrect password."
    return True, record


# =====================================================================
# REUSABLE UI HELPERS
# =====================================================================
def styled_entry(parent, show=None):
    entry = tk.Entry(
        parent, font=(Theme.FONT, 11), relief="flat",
        bg="#F4F7FE", fg=Theme.TEXT_DARK, insertbackground=Theme.TEXT_DARK,
        highlightthickness=1, highlightbackground=Theme.BORDER,
        highlightcolor=Theme.PURPLE, show=show,
    )
    entry.configure(bd=8)
    return entry


def rounded_button(parent, text, command, bg=None, fg="white", width=None):
    bg = bg or Theme.PURPLE
    btn = tk.Button(
        parent, text=text, command=command, bg=bg, fg=fg,
        activebackground=bg, activeforeground=fg,
        font=(Theme.FONT, 11, "bold"), relief="flat", bd=0,
        cursor="hand2", width=width, padx=10, pady=10,
    )
    return btn


# =====================================================================
# AUTH WINDOW (Login / Register)
# =====================================================================
class AuthWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("M-Store Admin - Sign In")
        self.geometry("420x560")
        self.configure(bg=Theme.MAIN_BG)
        self.resizable(False, False)
        self.eval("tk::PlaceWindow . center")

        self.mode = tk.StringVar(value="login")
        self._build_ui()

    # -----------------------------------------------------------
    def _build_ui(self):
        card = tk.Frame(self, bg=Theme.CARD_BG, padx=30, pady=30)
        card.place(relx=0.5, rely=0.5, anchor="center")

        # brand
        brandRow = tk.Frame(card, bg=Theme.CARD_BG)
        brandRow.pack(pady=(0, 20))
        badge = tk.Label(brandRow, text="M", bg=Theme.PURPLE, fg="white",
                          font=(Theme.FONT, 14, "bold"), width=2, height=1)
        badge.pack(side="left", padx=(0, 8))
        titleFrame = tk.Frame(brandRow, bg=Theme.CARD_BG)
        titleFrame.pack(side="left")
        tk.Label(titleFrame, text="M-Store Admin", bg=Theme.CARD_BG, fg=Theme.TEXT_DARK,
                  font=(Theme.FONT, 13, "bold")).pack(anchor="w")
        tk.Label(titleFrame, text="E-commerce Backend", bg=Theme.CARD_BG, fg=Theme.TEXT_MUTED,
                  font=(Theme.FONT, 8)).pack(anchor="w")

        # toggle
        toggleFrame = tk.Frame(card, bg="#F4F7FE")
        toggleFrame.pack(fill="x", pady=(0, 20))

        self.loginTabBtn = tk.Button(
            toggleFrame, text="Login", relief="flat", bd=0, font=(Theme.FONT, 10, "bold"),
            command=lambda: self._switch_mode("login")
        )
        self.registerTabBtn = tk.Button(
            toggleFrame, text="Create Account", relief="flat", bd=0, font=(Theme.FONT, 10, "bold"),
            command=lambda: self._switch_mode("register")
        )
        self.loginTabBtn.pack(side="left", fill="x", expand=True, ipady=8)
        self.registerTabBtn.pack(side="left", fill="x", expand=True, ipady=8)

        # form container (login + register frames stacked, only one shown)
        self.formContainer = tk.Frame(card, bg=Theme.CARD_BG)
        self.formContainer.pack(fill="both", expand=True)

        self.errorLabel = tk.Label(card, text="", bg=Theme.CARD_BG, fg=Theme.RED,
                                    font=(Theme.FONT, 9), wraplength=300, justify="left")
        self.errorLabel.pack(pady=(10, 0), anchor="w")

        self._build_login_form()
        self._build_register_form()
        self._switch_mode("login")

    # -----------------------------------------------------------
    def _field_label(self, parent, text):
        tk.Label(parent, text=text, bg=Theme.CARD_BG, fg=Theme.TEXT_DARK,
                  font=(Theme.FONT, 9, "bold")).pack(anchor="w", pady=(10, 3))

    def _build_login_form(self):
        self.loginFrame = tk.Frame(self.formContainer, bg=Theme.CARD_BG)

        self._field_label(self.loginFrame, "Username")
        self.loginUsername = styled_entry(self.loginFrame)
        self.loginUsername.pack(fill="x", ipady=6)

        self._field_label(self.loginFrame, "Password")
        self.loginPassword = styled_entry(self.loginFrame, show="*")
        self.loginPassword.pack(fill="x", ipady=6)

        rounded_button(self.loginFrame, "Sign In", self._handle_login).pack(
            fill="x", pady=(25, 0)
        )

        hint = tk.Label(self.loginFrame, text="No account yet? Use \"Create Account\" above.",
                         bg=Theme.CARD_BG, fg=Theme.TEXT_MUTED, font=(Theme.FONT, 8))
        hint.pack(pady=(15, 0))

        self.loginPassword.bind("<Return>", lambda e: self._handle_login())

    def _build_register_form(self):
        self.registerFrame = tk.Frame(self.formContainer, bg=Theme.CARD_BG)

        self._field_label(self.registerFrame, "Username")
        self.regUsername = styled_entry(self.registerFrame)
        self.regUsername.pack(fill="x", ipady=6)

        self._field_label(self.registerFrame, "Email")
        self.regEmail = styled_entry(self.registerFrame)
        self.regEmail.pack(fill="x", ipady=6)

        self._field_label(self.registerFrame, "Password")
        self.regPassword = styled_entry(self.registerFrame, show="*")
        self.regPassword.pack(fill="x", ipady=6)

        self._field_label(self.registerFrame, "Confirm Password")
        self.regConfirm = styled_entry(self.registerFrame, show="*")
        self.regConfirm.pack(fill="x", ipady=6)

        rounded_button(self.registerFrame, "Create Account", self._handle_register,
                        bg=Theme.GREEN).pack(fill="x", pady=(20, 0))

        self.regConfirm.bind("<Return>", lambda e: self._handle_register())

    # -----------------------------------------------------------
    def _switch_mode(self, mode):
        self.mode.set(mode)
        self.errorLabel.config(text="")
        self.loginFrame.pack_forget()
        self.registerFrame.pack_forget()

        if mode == "login":
            self.loginTabBtn.config(bg=Theme.PURPLE, fg="white")
            self.registerTabBtn.config(bg="#F4F7FE", fg=Theme.TEXT_MUTED)
            self.loginFrame.pack(fill="both", expand=True)
        else:
            self.registerTabBtn.config(bg=Theme.PURPLE, fg="white")
            self.loginTabBtn.config(bg="#F4F7FE", fg=Theme.TEXT_MUTED)
            self.registerFrame.pack(fill="both", expand=True)

    # -----------------------------------------------------------
    def _handle_login(self):
        username = self.loginUsername.get()
        password = self.loginPassword.get()
        ok, result = verify_user(username, password)
        if not ok:
            self.errorLabel.config(text=result)
            return
        self.destroy()
        app = Dashboard(admin_username=username, admin_record=result)
        app.mainloop()

    def _handle_register(self):
        username = self.regUsername.get()
        email = self.regEmail.get()
        password = self.regPassword.get()
        confirm = self.regConfirm.get()

        if password != confirm:
            self.errorLabel.config(text="Passwords do not match.")
            return

        ok, message = create_user(username, email, password)
        if not ok:
            self.errorLabel.config(text=message)
            return

        messagebox.showinfo("Success", "Account created. You can now sign in.")
        self._switch_mode("login")
        self.loginUsername.delete(0, "end")
        self.loginUsername.insert(0, username)
        self.regUsername.delete(0, "end")
        self.regEmail.delete(0, "end")
        self.regPassword.delete(0, "end")
        self.regConfirm.delete(0, "end")


# =====================================================================
# CHART DRAWING HELPERS (plain Canvas, no external chart library)
# =====================================================================
def draw_line_chart(canvas, values, labels, color=Theme.PURPLE):
    canvas.delete("all")
    w = int(canvas["width"])
    h = int(canvas["height"])
    padLeft, padRight, padTop, padBottom = 45, 15, 15, 25

    plotW = w - padLeft - padRight
    plotH = h - padTop - padBottom
    maxVal = max(values) * 1.2 if values else 1
    step = plotW / (len(values) - 1) if len(values) > 1 else plotW

    # horizontal grid lines + y labels
    for i in range(5):
        y = padTop + plotH - (plotH * i / 4)
        val = maxVal * i / 4
        canvas.create_line(padLeft, y, w - padRight, y, fill=Theme.BORDER)
        canvas.create_text(padLeft - 8, y, text=f"{int(val/1000)}K" if val >= 1000 else str(int(val)),
                            anchor="e", fill=Theme.TEXT_MUTED, font=(Theme.FONT, 8))

    points = []
    for i, v in enumerate(values):
        x = padLeft + step * i
        y = padTop + plotH - (v / maxVal * plotH)
        points.append((x, y))

    # filled area under the line
    if len(points) > 1:
        poly = [points[0][0], padTop + plotH]
        for p in points:
            poly.extend(p)
        poly.extend([points[-1][0], padTop + plotH])
        canvas.create_polygon(poly, fill="#EDE9FF", outline="")

        for i in range(len(points) - 1):
            canvas.create_line(*points[i], *points[i + 1], fill=color, width=2, smooth=True)

    for (x, y) in points:
        canvas.create_oval(x - 3, y - 3, x + 3, y + 3, fill=color, outline="white", width=1)

    for i, lbl in enumerate(labels):
        x = padLeft + step * i
        canvas.create_text(x, h - padBottom + 12, text=lbl, fill=Theme.TEXT_MUTED, font=(Theme.FONT, 8))


def draw_donut_chart(canvas, segments, center_text_top, center_text_bottom):
    """segments: list of (label, value, color)"""
    canvas.delete("all")
    w = int(canvas["width"])
    h = int(canvas["height"])
    cx, cy = w / 2, h / 2
    outerR = min(w, h) / 2 - 5
    innerR = outerR * 0.55

    total = sum(v for _, v, _ in segments) or 1
    start = 90.0
    for label, value, color in segments:
        extent = -360.0 * (value / total)
        canvas.create_arc(
            cx - outerR, cy - outerR, cx + outerR, cy + outerR,
            start=start, extent=extent, fill=color, outline=Theme.CARD_BG, width=2, style="pieslice",
        )
        start += extent

    # punch the hole to make it a donut
    canvas.create_oval(cx - innerR, cy - innerR, cx + innerR, cy + innerR,
                        fill=Theme.CARD_BG, outline=Theme.CARD_BG)

    canvas.create_text(cx, cy - 8, text=center_text_top, font=(Theme.FONT, 16, "bold"), fill=Theme.TEXT_DARK)
    canvas.create_text(cx, cy + 12, text=center_text_bottom, font=(Theme.FONT, 8), fill=Theme.TEXT_MUTED)


# =====================================================================
# DEMO DATA (stands in for a real backend/database)
# =====================================================================
def generate_demo_data():
    today = datetime.now()
    days = [(today - timedelta(days=i)).strftime("%b %d") for i in range(6, -1, -1)]
    sales = [random.randint(180, 650) * 1000 for _ in range(7)]

    orders_status = [
        ("Pending", random.randint(30, 55), Theme.ORANGE),
        ("Processing", random.randint(35, 60), Theme.BLUE),
        ("Shipped", random.randint(20, 45), Theme.GREEN),
        ("Delivered", random.randint(10, 25), Theme.PURPLE),
        ("Cancelled", random.randint(1, 8), Theme.RED),
    ]

    categories = [
        ("Electronics", 45, Theme.PURPLE),
        ("Fashion", 25, Theme.BLUE),
        ("Home & Kitchen", 15, Theme.GREEN),
        ("Beauty", 10, Theme.ORANGE),
        ("Others", 5, Theme.RED),
    ]

    customers = ["Brian Otieno", "Mercy Wanjiku", "Kevin Mutua", "Aisha Mohamed",
                 "Collins Kiprotich", "Lucy Njeri", "David Karanja", "Grace Mwangi",
                 "Peter Odhiambo", "Joyce Akinyi"]
    payments = ["M-Pesa", "Card", "Cash on Delivery"]
    statuses = ["Processing", "Pending", "Shipped", "Delivered"]

    orders = []
    for i in range(6):
        orders.append({
            "id": f"#ORD-{157 - i:06d}"[:10],
            "customer": random.choice(customers),
            "amount": f"KSh {random.randint(500, 15000):,}",
            "payment": random.choice(payments),
            "status": random.choice(statuses),
            "date": (today - timedelta(days=random.randint(0, 3))).strftime("%b %d, %Y"),
        })

    accounts = []
    for name in random.sample(customers, 5):
        email = name.lower().replace(" ", ".") + "@email.com"
        accounts.append({
            "user": name,
            "email": email,
            "joined": (today - timedelta(days=random.randint(0, 3))).strftime("%b %d, %Y"),
        })

    activity_templates = [
        ("New order placed", Theme.GREEN),
        ("New account registered", Theme.BLUE),
        ("Product updated", Theme.ORANGE),
        ("Payment received", Theme.PURPLE),
        ("Order cancelled", Theme.RED),
    ]
    activity = []
    for i in range(5):
        text, color = random.choice(activity_templates)
        activity.append((text, f"{random.randint(1, 59)} mins ago", color))

    return {
        "days": days,
        "sales": sales,
        "orders_status": orders_status,
        "categories": categories,
        "orders": orders,
        "accounts": accounts,
        "activity": activity,
        "total_sales": sum(sales),
        "new_orders": sum(v for _, v, _ in orders_status),
        "new_accounts": random.randint(60, 120),
        "products": random.randint(900, 1400),
    }


# =====================================================================
# DASHBOARD (main admin window)
# =====================================================================
class Dashboard(tk.Tk):
    def __init__(self, admin_username, admin_record):
        super().__init__()
        self.admin_username = admin_username
        self.admin_record = admin_record
        self.data = generate_demo_data()

        self.title("M-Store Admin - Dashboard")
        self.geometry("1280x820")
        self.configure(bg=Theme.MAIN_BG)
        self.minsize(1100, 700)

        self._build_layout()

    # -----------------------------------------------------------
    def _build_layout(self):
        root = tk.Frame(self, bg=Theme.MAIN_BG)
        root.pack(fill="both", expand=True)

        self._build_sidebar(root)

        rightSide = tk.Frame(root, bg=Theme.MAIN_BG)
        rightSide.pack(side="left", fill="both", expand=True)

        self._build_topbar(rightSide)

        body = tk.Frame(rightSide, bg=Theme.MAIN_BG, padx=25, pady=20)
        body.pack(fill="both", expand=True)

        tk.Label(body, text="Dashboard", bg=Theme.MAIN_BG, fg=Theme.TEXT_DARK,
                  font=(Theme.FONT, 20, "bold")).pack(anchor="w", pady=(0, 15))

        self._build_stat_cards(body)
        self._build_charts_row(body)
        self._build_tables_row(body)

        self._build_status_bar(rightSide)

    # -----------------------------------------------------------
    # SIDEBAR
    # -----------------------------------------------------------
    def _build_sidebar(self, parent):
        sidebar = tk.Frame(parent, bg=Theme.SIDEBAR_BG, width=230)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        brand = tk.Frame(sidebar, bg=Theme.SIDEBAR_BG)
        brand.pack(fill="x", pady=20, padx=20)
        badge = tk.Label(brand, text="M", bg=Theme.PURPLE, fg="white",
                          font=(Theme.FONT, 12, "bold"), width=2)
        badge.pack(side="left", padx=(0, 8))
        titleFrame = tk.Frame(brand, bg=Theme.SIDEBAR_BG)
        titleFrame.pack(side="left")
        tk.Label(titleFrame, text="M-Store Admin", bg=Theme.SIDEBAR_BG, fg="white",
                  font=(Theme.FONT, 11, "bold")).pack(anchor="w")
        tk.Label(titleFrame, text="E-commerce Backend", bg=Theme.SIDEBAR_BG, fg=Theme.SIDEBAR_TEXT,
                  font=(Theme.FONT, 7)).pack(anchor="w")

        sections = [
            (None, [("Dashboard", True)]),
            ("ORDERS", [("Orders", False), ("Returns & Refunds", False), ("Transactions", False)]),
            ("CUSTOMERS", [("Accounts", False), ("Roles & Permissions", False)]),
            ("PRODUCTS", [("Products", False), ("Categories", False), ("Brands", False), ("Inventory", False)]),
            ("MARKETING", [("Coupons", False), ("Banners", False), ("Flash Sales", False)]),
            ("SETTINGS", [("Payment Methods", False), ("Shipping", False), ("General Settings", False), ("Logs", False)]),
        ]

        navArea = tk.Frame(sidebar, bg=Theme.SIDEBAR_BG)
        navArea.pack(fill="both", expand=True)

        for section_title, items in sections:
            if section_title:
                tk.Label(navArea, text=section_title, bg=Theme.SIDEBAR_BG, fg=Theme.SIDEBAR_TEXT,
                          font=(Theme.FONT, 7, "bold")).pack(anchor="w", padx=20, pady=(14, 4))
            for label, active in items:
                self._sidebar_item(navArea, label, active)

        logoutBtn = tk.Button(
            sidebar, text="\u2192  Logout", bg="#2B3667", fg="white", relief="flat",
            bd=0, font=(Theme.FONT, 10, "bold"), anchor="w", padx=20, pady=10,
            activebackground="#3a4680", activeforeground="white",
            command=self._logout,
        )
        logoutBtn.pack(fill="x", side="bottom", padx=15, pady=15)

    def _sidebar_item(self, parent, label, active):
        bg = Theme.SIDEBAR_ACTIVE if active else Theme.SIDEBAR_BG
        fg = Theme.SIDEBAR_TEXT_ACTIVE if active else Theme.SIDEBAR_TEXT
        item = tk.Button(
            parent, text=label, bg=bg, fg=fg, relief="flat", bd=0,
            anchor="w", padx=20, pady=8, font=(Theme.FONT, 9),
            activebackground=Theme.SIDEBAR_ACTIVE, activeforeground="white",
            command=lambda: messagebox.showinfo(label, f"\"{label}\" screen not built yet."),
        )
        item.pack(fill="x", padx=10, pady=1)

    # -----------------------------------------------------------
    # TOP BAR
    # -----------------------------------------------------------
    def _build_topbar(self, parent):
        topbar = tk.Frame(parent, bg=Theme.CARD_BG, height=60)
        topbar.pack(fill="x")
        topbar.pack_propagate(False)

        searchFrame = tk.Frame(topbar, bg="#F4F7FE")
        searchFrame.pack(side="left", padx=25, pady=12, ipady=4)
        tk.Label(searchFrame, text="\U0001F50D", bg="#F4F7FE").pack(side="left", padx=(10, 4))
        searchEntry = tk.Entry(searchFrame, bg="#F4F7FE", relief="flat", width=40,
                                font=(Theme.FONT, 10), fg=Theme.TEXT_MUTED)
        searchEntry.insert(0, "Search for orders, customers, products...")
        searchEntry.pack(side="left", ipady=4, padx=(0, 10))

        profileFrame = tk.Frame(topbar, bg=Theme.CARD_BG)
        profileFrame.pack(side="right", padx=25)

        avatar = tk.Label(profileFrame, text=self.admin_username[:1].upper(), bg=Theme.PURPLE,
                           fg="white", font=(Theme.FONT, 10, "bold"), width=3, height=1)
        avatar.pack(side="right", padx=(10, 0))

        nameFrame = tk.Frame(profileFrame, bg=Theme.CARD_BG)
        nameFrame.pack(side="right")
        tk.Label(nameFrame, text=self.admin_username, bg=Theme.CARD_BG, fg=Theme.TEXT_DARK,
                  font=(Theme.FONT, 9, "bold")).pack(anchor="e")
        tk.Label(nameFrame, text="Admin", bg=Theme.CARD_BG, fg=Theme.TEXT_MUTED,
                  font=(Theme.FONT, 8)).pack(anchor="e")

        for icon in ("\U0001F514", "\u2709", "\u2753"):
            tk.Label(profileFrame, text=icon, bg=Theme.CARD_BG, fg=Theme.TEXT_DARK,
                      font=(Theme.FONT, 12)).pack(side="right", padx=8)

    # -----------------------------------------------------------
    # STAT CARDS
    # -----------------------------------------------------------
    def _build_stat_cards(self, parent):
        row = tk.Frame(parent, bg=Theme.MAIN_BG)
        row.pack(fill="x", pady=(0, 15))
        for i in range(4):
            row.columnconfigure(i, weight=1)

        d = self.data
        cards = [
            ("Total Sales", f"KSh {d['total_sales']:,}", "+18.6%", "vs last 3 days", Theme.PURPLE, "\U0001F4B0"),
            ("New Orders", str(d["new_orders"]), "+22.4%", "vs last 3 days", Theme.BLUE, "\U0001F6CD"),
            ("New Accounts", str(d["new_accounts"]), "+35.7%", "vs last 3 days", Theme.GREEN, "\U0001F464"),
            ("Products", str(d["products"]), "+8.3%", "vs last 3 days", Theme.ORANGE, "\U0001F4E6"),
        ]

        for i, (title, value, delta, sub, color, icon) in enumerate(cards):
            card = tk.Frame(row, bg=Theme.CARD_BG, padx=18, pady=15,
                             highlightbackground=Theme.BORDER, highlightthickness=1)
            card.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 8, 0))

            top = tk.Frame(card, bg=Theme.CARD_BG)
            top.pack(fill="x")
            tk.Label(top, text=title, bg=Theme.CARD_BG, fg=Theme.TEXT_MUTED,
                      font=(Theme.FONT, 9)).pack(side="left")
            tk.Label(top, text=icon, bg=color, fg="white", font=(Theme.FONT, 10),
                      width=3, height=1).pack(side="right")

            tk.Label(card, text=value, bg=Theme.CARD_BG, fg=Theme.TEXT_DARK,
                      font=(Theme.FONT, 18, "bold")).pack(anchor="w", pady=(8, 2))

            bottom = tk.Frame(card, bg=Theme.CARD_BG)
            bottom.pack(fill="x")
            tk.Label(bottom, text=f"\u2191 {delta}", bg=Theme.CARD_BG, fg=Theme.GREEN,
                      font=(Theme.FONT, 8, "bold")).pack(side="left")
            tk.Label(bottom, text=f"  {sub}", bg=Theme.CARD_BG, fg=Theme.TEXT_MUTED,
                      font=(Theme.FONT, 8)).pack(side="left")

    # -----------------------------------------------------------
    # CHARTS ROW
    # -----------------------------------------------------------
    def _build_charts_row(self, parent):
        row = tk.Frame(parent, bg=Theme.MAIN_BG)
        row.pack(fill="x", pady=(0, 15))
        row.columnconfigure(0, weight=2)
        row.columnconfigure(1, weight=1)
        row.columnconfigure(2, weight=1)

        d = self.data

        # --- Sales Overview (line chart) ---
        salesCard = tk.Frame(row, bg=Theme.CARD_BG, padx=15, pady=15,
                              highlightbackground=Theme.BORDER, highlightthickness=1)
        salesCard.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        tk.Label(salesCard, text="Sales Overview", bg=Theme.CARD_BG, fg=Theme.TEXT_DARK,
                  font=(Theme.FONT, 11, "bold")).pack(anchor="w")
        salesCanvas = tk.Canvas(salesCard, width=430, height=220, bg=Theme.CARD_BG, highlightthickness=0)
        salesCanvas.pack(pady=(10, 0))
        draw_line_chart(salesCanvas, d["sales"], d["days"], color=Theme.PURPLE)

        # --- Orders Overview (donut chart) ---
        ordersCard = tk.Frame(row, bg=Theme.CARD_BG, padx=15, pady=15,
                               highlightbackground=Theme.BORDER, highlightthickness=1)
        ordersCard.grid(row=0, column=1, sticky="nsew", padx=8)
        tk.Label(ordersCard, text="Orders Overview", bg=Theme.CARD_BG, fg=Theme.TEXT_DARK,
                  font=(Theme.FONT, 11, "bold")).pack(anchor="w")

        donutRow = tk.Frame(ordersCard, bg=Theme.CARD_BG)
        donutRow.pack(fill="both", expand=True, pady=(10, 0))

        donutCanvas = tk.Canvas(donutRow, width=140, height=140, bg=Theme.CARD_BG, highlightthickness=0)
        donutCanvas.pack(side="left")
        segments = [(label, val, color) for label, val, color in d["orders_status"]]
        draw_donut_chart(donutCanvas, segments, str(d["new_orders"]), "Total")

        legend = tk.Frame(donutRow, bg=Theme.CARD_BG)
        legend.pack(side="left", padx=(15, 0), fill="y")
        total = sum(v for _, v, _ in segments) or 1
        for label, val, color in segments:
            r = tk.Frame(legend, bg=Theme.CARD_BG)
            r.pack(anchor="w", pady=3)
            tk.Label(r, text="\u25CF", fg=color, bg=Theme.CARD_BG, font=(Theme.FONT, 10)).pack(side="left")
            tk.Label(r, text=f" {label}", fg=Theme.TEXT_DARK, bg=Theme.CARD_BG,
                      font=(Theme.FONT, 8)).pack(side="left")
            tk.Label(r, text=f"  {val} ({round(val/total*100)}%)", fg=Theme.TEXT_MUTED, bg=Theme.CARD_BG,
                      font=(Theme.FONT, 8)).pack(side="left")

        # --- Top Selling Categories ---
        catCard = tk.Frame(row, bg=Theme.CARD_BG, padx=15, pady=15,
                            highlightbackground=Theme.BORDER, highlightthickness=1)
        catCard.grid(row=0, column=2, sticky="nsew", padx=(8, 0))
        tk.Label(catCard, text="Top Selling Categories", bg=Theme.CARD_BG, fg=Theme.TEXT_DARK,
                  font=(Theme.FONT, 11, "bold")).pack(anchor="w", pady=(0, 10))

        for label, pct, color in d["categories"]:
            r = tk.Frame(catCard, bg=Theme.CARD_BG)
            r.pack(fill="x", pady=6)
            top = tk.Frame(r, bg=Theme.CARD_BG)
            top.pack(fill="x")
            tk.Label(top, text=label, bg=Theme.CARD_BG, fg=Theme.TEXT_DARK,
                      font=(Theme.FONT, 9)).pack(side="left")
            tk.Label(top, text=f"{pct}%", bg=Theme.CARD_BG, fg=Theme.TEXT_MUTED,
                      font=(Theme.FONT, 8)).pack(side="right")

            barBg = tk.Frame(r, bg=Theme.BORDER, height=6)
            barBg.pack(fill="x", pady=(4, 0))
            barBg.pack_propagate(False)
            barFill = tk.Frame(barBg, bg=color)
            barFill.place(relx=0, rely=0, relwidth=pct / 100, relheight=1)

    # -----------------------------------------------------------
    # TABLES ROW
    # -----------------------------------------------------------
    def _build_tables_row(self, parent):
        row = tk.Frame(parent, bg=Theme.MAIN_BG)
        row.pack(fill="both", expand=True)
        row.columnconfigure(0, weight=2)
        row.columnconfigure(1, weight=1)
        row.columnconfigure(2, weight=1)

        d = self.data

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Dash.Treeview", background=Theme.CARD_BG, fieldbackground=Theme.CARD_BG,
                        rowheight=28, font=(Theme.FONT, 9), borderwidth=0)
        style.configure("Dash.Treeview.Heading", background=Theme.CARD_BG, foreground=Theme.TEXT_MUTED,
                        font=(Theme.FONT, 8, "bold"), borderwidth=0)
        style.map("Dash.Treeview", background=[("selected", "#EDE9FF")])

        # --- Recent Orders ---
        ordersCard = tk.Frame(row, bg=Theme.CARD_BG, padx=15, pady=15,
                               highlightbackground=Theme.BORDER, highlightthickness=1)
        ordersCard.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=(0, 8))
        tk.Label(ordersCard, text="Recent Orders", bg=Theme.CARD_BG, fg=Theme.TEXT_DARK,
                  font=(Theme.FONT, 11, "bold")).pack(anchor="w", pady=(0, 8))

        cols = ("id", "customer", "amount", "payment", "status", "date")
        tree = ttk.Treeview(ordersCard, columns=cols, show="headings", height=6, style="Dash.Treeview")
        headings = {"id": "Order ID", "customer": "Customer", "amount": "Amount",
                    "payment": "Payment", "status": "Status", "date": "Date"}
        for c in cols:
            tree.heading(c, text=headings[c])
            tree.column(c, width=90, anchor="w")
        for o in d["orders"]:
            tree.insert("", "end", values=(o["id"], o["customer"], o["amount"], o["payment"], o["status"], o["date"]))
        tree.pack(fill="both", expand=True)

        # --- New Accounts ---
        accCard = tk.Frame(row, bg=Theme.CARD_BG, padx=15, pady=15,
                            highlightbackground=Theme.BORDER, highlightthickness=1)
        accCard.grid(row=0, column=1, sticky="nsew", padx=8, pady=(0, 8))
        tk.Label(accCard, text="New Accounts", bg=Theme.CARD_BG, fg=Theme.TEXT_DARK,
                  font=(Theme.FONT, 11, "bold")).pack(anchor="w", pady=(0, 8))

        for a in d["accounts"]:
            r = tk.Frame(accCard, bg=Theme.CARD_BG)
            r.pack(fill="x", pady=4)
            tk.Label(r, text=a["user"][:1], bg=Theme.BLUE, fg="white",
                      font=(Theme.FONT, 8, "bold"), width=2).pack(side="left")
            info = tk.Frame(r, bg=Theme.CARD_BG)
            info.pack(side="left", padx=8)
            tk.Label(info, text=a["user"], bg=Theme.CARD_BG, fg=Theme.TEXT_DARK,
                      font=(Theme.FONT, 8, "bold")).pack(anchor="w")
            tk.Label(info, text=a["email"], bg=Theme.CARD_BG, fg=Theme.TEXT_MUTED,
                      font=(Theme.FONT, 7)).pack(anchor="w")
            tk.Label(r, text=a["joined"], bg=Theme.CARD_BG, fg=Theme.TEXT_MUTED,
                      font=(Theme.FONT, 7)).pack(side="right")

        # --- System Activity ---
        actCard = tk.Frame(row, bg=Theme.CARD_BG, padx=15, pady=15,
                            highlightbackground=Theme.BORDER, highlightthickness=1)
        actCard.grid(row=0, column=2, sticky="nsew", padx=(8, 0), pady=(0, 8))
        tk.Label(actCard, text="System Activity", bg=Theme.CARD_BG, fg=Theme.TEXT_DARK,
                  font=(Theme.FONT, 11, "bold")).pack(anchor="w", pady=(0, 8))

        for text, when, color in d["activity"]:
            r = tk.Frame(actCard, bg=Theme.CARD_BG)
            r.pack(fill="x", pady=5)
            tk.Label(r, text="\u25CF", fg=color, bg=Theme.CARD_BG, font=(Theme.FONT, 10)).pack(side="left")
            info = tk.Frame(r, bg=Theme.CARD_BG)
            info.pack(side="left", padx=6)
            tk.Label(info, text=text, bg=Theme.CARD_BG, fg=Theme.TEXT_DARK,
                      font=(Theme.FONT, 8)).pack(anchor="w")
            tk.Label(info, text=when, bg=Theme.CARD_BG, fg=Theme.TEXT_MUTED,
                      font=(Theme.FONT, 7)).pack(anchor="w")

    # -----------------------------------------------------------
    # STATUS BAR
    # -----------------------------------------------------------
    def _build_status_bar(self, parent):
        bar = tk.Frame(parent, bg=Theme.SIDEBAR_BG, height=45)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)

        stats = [
            ("Server Status", "Online", Theme.GREEN),
            ("Total Users", "12,458", None),
            ("Active Users (Now)", "258", Theme.GREEN),
            ("Total Orders", "8,745", None),
            ("Pending Orders", "45", None),
            ("Database", "Connected", Theme.GREEN),
            ("Backup", "Up to date", None),
        ]
        for label, value, color in stats:
            block = tk.Frame(bar, bg=Theme.SIDEBAR_BG)
            block.pack(side="left", padx=20, pady=8)
            tk.Label(block, text=label, bg=Theme.SIDEBAR_BG, fg=Theme.SIDEBAR_TEXT,
                      font=(Theme.FONT, 7)).pack(anchor="w")
            tk.Label(block, text=value, bg=Theme.SIDEBAR_BG, fg=color or "white",
                      font=(Theme.FONT, 8, "bold")).pack(anchor="w")

    # -----------------------------------------------------------
    def _logout(self):
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            self.destroy()
            auth = AuthWindow()
            auth.mainloop()


# =====================================================================
# ENTRY POINT
# =====================================================================
def main():
    auth = AuthWindow()
    auth.mainloop()


if __name__ == "__main__":
    main()