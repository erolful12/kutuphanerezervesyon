import datetime
import os
import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import Calendar

# Dosya yollarını tanımla
DATABASE_FOLDER = "database"
USERS_FILE = os.path.join(DATABASE_FOLDER, "users.txt")
BOOKS_FILE = os.path.join(DATABASE_FOLDER, "books.txt")
TABLES_FILE = os.path.join(DATABASE_FOLDER, "tables.txt")
BOOK_RESERVATIONS_FILE = os.path.join(DATABASE_FOLDER, "book_reservations.txt")
TABLE_RESERVATIONS_FILE = os.path.join(DATABASE_FOLDER, "table_reservations.txt")
ADMIN_CREDENTIALS = ("admin", "admin123")


def ensure_database_folder():
    if not os.path.exists(DATABASE_FOLDER):
        os.makedirs(DATABASE_FOLDER)


def initialize_files():
    ensure_database_folder()
    files = [
        USERS_FILE,
        BOOKS_FILE,
        TABLES_FILE,
        BOOK_RESERVATIONS_FILE,
        TABLE_RESERVATIONS_FILE,
    ]
    for file_path in files:
        if not os.path.exists(file_path):
            with open(file_path, "w") as f:
                pass


def load_data(file_path, parser):
    data = []
    with open(file_path, "r") as f:
        for line in f:
            data.append(parser(line.strip()))
    return data


def save_data(file_path, data, formatter):
    with open(file_path, "w") as f:
        for item in data:
            f.write(formatter(item) + "\n")


# Rezervasyon çakışma kontrolleri
def check_book_conflict(book_name, date):
    reservations = load_data(BOOK_RESERVATIONS_FILE, lambda line: line.split(","))
    return any(res[1] == book_name and res[2] == str(date) for res in reservations)


def check_table_conflict(table_id, date, start_time, end_time):
    reservations = load_data(TABLE_RESERVATIONS_FILE, lambda line: line.split(","))
    start = datetime.datetime.strptime(start_time, "%H:%M").time()
    end = datetime.datetime.strptime(end_time, "%H:%M").time()
    for res in reservations:
        if res[1] == table_id and res[2] == str(date):
            res_start = datetime.datetime.strptime(res[3], "%H:%M").time()
            res_end = datetime.datetime.strptime(res[4], "%H:%M").time()
            if (start < res_end) and (end > res_start):
                return True
    return False


# Rezervasyon iptali
def cancel_reservation(file_path, reservation_data):
    data = load_data(file_path, lambda line: line.split(","))
    updated_data = [d for d in data if d != reservation_data]
    save_data(file_path, updated_data, lambda x: ",".join(x))


# Admin paneli
def admin_panel(window):
    def delete_item(file_path, item):
        data = load_data(file_path, lambda line: line.split(","))
        updated_data = [d for d in data if d != item]
        save_data(file_path, updated_data, lambda x: ",".join(x))
        refresh_all()

    def refresh_all():
        books = load_data(BOOKS_FILE, lambda line: line.split(","))
        book_list.delete(0, tk.END)
        for book in books:
            book_list.insert(tk.END, f"{book[0]} - {book[1]}")

        tables = load_data(TABLES_FILE, lambda line: line.split(","))
        table_list.delete(0, tk.END)
        for table in tables:
            table_list.insert(tk.END, f"Masa {table[0]} - Kapasite: {table[1]}")

        book_res = load_data(BOOK_RESERVATIONS_FILE, lambda line: line.split(","))
        table_res = load_data(TABLE_RESERVATIONS_FILE, lambda line: line.split(","))
        reservation_list.delete(0, tk.END)
        for res in book_res + table_res:
            reservation_list.insert(tk.END, " | ".join(res))

    admin_window = tk.Toplevel(window)
    admin_window.title("Admin Paneli")
    admin_window.geometry("800x600")

    notebook = ttk.Notebook(admin_window)
    notebook.pack(fill=tk.BOTH, expand=True)

    # Kitaplar sekmesi
    book_frame = ttk.Frame(notebook)
    book_list = tk.Listbox(book_frame)
    book_list.pack(fill=tk.BOTH, expand=True)
    tk.Button(
        book_frame,
        text="Sil",
        command=lambda: delete_item(
            BOOKS_FILE, book_list.get(book_list.curselection()).split(" - ")
        ),
    ).pack()
    notebook.add(book_frame, text="Kitaplar")

    # Masalar sekmesi
    table_frame = ttk.Frame(notebook)
    table_list = tk.Listbox(table_frame)
    table_list.pack(fill=tk.BOTH, expand=True)
    tk.Button(
        table_frame,
        text="Sil",
        command=lambda: delete_item(
            TABLES_FILE, table_list.get(table_list.curselection()).split(" - ")
        ),
    ).pack()
    notebook.add(table_frame, text="Masalar")

    # Rezervasyonlar sekmesi
    res_frame = ttk.Frame(notebook)
    reservation_list = tk.Listbox(res_frame)
    reservation_list.pack(fill=tk.BOTH, expand=True)
    tk.Button(
        res_frame,
        text="Sil",
        command=lambda: [
            cancel_reservation(
                BOOK_RESERVATIONS_FILE,
                reservation_list.get(reservation_list.curselection()).split(" | "),
            ),
            cancel_reservation(
                TABLE_RESERVATIONS_FILE,
                reservation_list.get(reservation_list.curselection()).split(" | "),
            ),
        ],
    ).pack()
    notebook.add(res_frame, text="Tüm Rezervasyonlar")

    refresh_all()


def admin_login(window):
    def check_admin():
        if (
            username_entry.get() == ADMIN_CREDENTIALS[0]
            and password_entry.get() == ADMIN_CREDENTIALS[1]
        ):
            admin_panel(login_window)
            login_window.destroy()
        else:
            messagebox.showerror("Hata", "Geçersiz admin bilgileri!")

    login_window = tk.Toplevel(window)
    login_window.title("Admin Girişi")
    login_window.geometry("300x150")

    tk.Label(login_window, text="Kullanıcı Adı:").grid(
        row=0, column=0, padx=10, pady=5
    )
    username_entry = tk.Entry(login_window)
    username_entry.grid(row=0, column=1, padx=10, pady=5)

    tk.Label(login_window, text="Şifre:").grid(row=1, column=0, padx=10, pady=5)
    password_entry = tk.Entry(login_window, show="*")
    password_entry.grid(row=1, column=1, padx=10, pady=5)

    tk.Button(login_window, text="Giriş Yap", command=check_admin).grid(
        row=2, column=0, columnspan=2, pady=10
    )


def register_user(window):
    def register():
        student_id = student_id_entry.get()
        password = password_entry.get()
        if not student_id or not password:
            messagebox.showerror("Hata", "Öğrenci numarası ve şifre gerekli.")
            return
        users = load_data(USERS_FILE, lambda line: line.split(","))
        if any(user[0] == student_id for user in users):
            messagebox.showerror("Hata", "Kullanıcı zaten kayıtlı.")
            return
        users.append((student_id, password))
        save_data(USERS_FILE, users, lambda user: ",".join(user))
        messagebox.showinfo("Başarılı", "Kayıt başarılı.")
        register_window.destroy()

    register_window = tk.Toplevel(window)
    register_window.title("Kaydol")
    register_window.geometry("300x200")

    tk.Label(register_window, text="Öğrenci Numarası:").grid(
        row=0, column=0, padx=10, pady=10
    )
    student_id_entry = tk.Entry(register_window)
    student_id_entry.grid(row=0, column=1, padx=10, pady=10)

    tk.Label(register_window, text="Şifre:").grid(row=1, column=0, padx=10, pady=10)
    password_entry = tk.Entry(register_window, show="*")
    password_entry.grid(row=1, column=1, padx=10, pady=10)

    tk.Button(register_window, text="Kaydol", command=register).grid(
        row=2, column=0, columnspan=2, pady=10
    )
    tk.Button(
        register_window, text="Giriş Ekranına Dön", command=register_window.destroy
    ).grid(row=3, column=0, columnspan=2, pady=10)


def login_user(window):
    def login():
        global logged_in_user
        student_id = student_id_entry.get()
        password = password_entry.get()
        users = load_data(USERS_FILE, lambda line: line.split(","))
        if any(user[0] == student_id and user[1] == password for user in users):
            logged_in_user = student_id
            window.destroy()
            main_menu(tk.Tk())
        else:
            messagebox.showerror("Hata", "Hatalı öğrenci numarası veya şifre.")

    login_window = tk.Toplevel(window)
    login_window.title("Giriş Yap")
    login_window.geometry("300x200")

    tk.Label(login_window, text="Öğrenci Numarası:").grid(
        row=0, column=0, padx=10, pady=10
    )
    student_id_entry = tk.Entry(login_window)
    student_id_entry.grid(row=0, column=1, padx=10, pady=10)

    tk.Label(login_window, text="Şifre:").grid(row=1, column=0, padx=10, pady=10)
    password_entry = tk.Entry(login_window, show="*")
    password_entry.grid(row=1, column=1, padx=10, pady=10)

    tk.Button(login_window, text="Giriş Yap", command=login).grid(
        row=2, column=0, columnspan=2, pady=10
    )


def add_book(window):
    def add():
        book_name = book_name_entry.get()
        author_name = author_name_entry.get()
        if not book_name or not author_name:
            messagebox.showerror("Hata", "Kitap adı ve yazar adı gerekli.")
            return
        books = load_data(BOOKS_FILE, lambda line: line.split(","))
        books.append((book_name, author_name))
        save_data(BOOKS_FILE, books, lambda book: ",".join(book))
        messagebox.showinfo("Başarılı", "Kitap başarıyla eklendi.")
        add_book_window.destroy()

    add_book_window = tk.Toplevel(window)
    add_book_window.title("Kitap Ekle")
    add_book_window.geometry("300x200")

    tk.Label(add_book_window, text="Kitap Adı:").grid(
        row=0, column=0, padx=10, pady=10
    )
    book_name_entry = tk.Entry(add_book_window)
    book_name_entry.grid(row=0, column=1, padx=10, pady=10)

    tk.Label(add_book_window, text="Yazar Adı:").grid(
        row=1, column=0, padx=10, pady=10
    )
    author_name_entry = tk.Entry(add_book_window)
    author_name_entry.grid(row=1, column=1, padx=10, pady=10)

    tk.Button(add_book_window, text="Ekle", command=add).grid(
        row=2, column=0, columnspan=2, pady=10
    )


def add_table(window):
    def add():
        capacity = capacity_entry.get()
        if not capacity:
            messagebox.showerror("Hata", "Masa kapasitesi gerekli.")
            return
        try:
            capacity = int(capacity)
        except ValueError:
            messagebox.showerror("Hata", "Kapasite sayı olmalıdır.")
            return
        tables = load_data(TABLES_FILE, lambda line: line.split(","))
        tables.append((len(tables) + 1, str(capacity)))
        save_data(TABLES_FILE, tables, lambda table: ",".join(map(str, table)))
        messagebox.showinfo("Başarılı", "Masa başarıyla eklendi.")
        add_table_window.destroy()

    add_table_window = tk.Toplevel(window)
    add_table_window.title("Masa Ekle")
    add_table_window.geometry("300x200")

    tk.Label(add_table_window, text="Kapasite:").grid(
        row=0, column=0, padx=10, pady=10
    )
    capacity_entry = tk.Entry(add_table_window)
    capacity_entry.grid(row=0, column=1, padx=10, pady=10)

    tk.Button(add_table_window, text="Ekle", command=add).grid(
        row=1, column=0, columnspan=2, pady=10
    )


def book_reservation(window):
    def select_date():
        def on_date_selected():
            nonlocal date_str
            date_str = cal.get_date()
            date_label.config(text="Seçilen Tarih: " + date_str)
            top.destroy()
            reserve(date_str)

        top = tk.Toplevel(book_reservation_window)
        top.title("Tarih Seç")
        cal = Calendar(
            top,
            selectmode="day",
            year=datetime.date.today().year,
            month=datetime.date.today().month,
            day=datetime.date.today().day,
            mindate=datetime.date.today(),
            maxdate=datetime.date.today() + datetime.timedelta(days=14),
            date_pattern='dd.mm.yyyy'  # Tarih formatı burada belirlendi
        )
        cal.pack(pady=20)
        tk.Button(top, text="Onayla", command=on_date_selected).pack()

    def reserve(date_str):
        try:
            selected_index = listbox.curselection()[0]
            selected_book = books[selected_index]
            if check_book_conflict(selected_book[0], date_str):
                messagebox.showerror("Hata", "Bu kitap zaten o tarihte rezerve edilmiş!")
                return
            # Aşağıdaki satırı düzeltin:
            reservation_date = datetime.datetime.strptime(date_str, "%d.%m.%Y").date()
            reservations = load_data(BOOK_RESERVATIONS_FILE, lambda line: line.split(","))
            reservations.append((logged_in_user, selected_book[0], str(reservation_date)))
            save_data(BOOK_RESERVATIONS_FILE, reservations, lambda res: ",".join(res))
            messagebox.showinfo("Başarılı", "Kitap rezervasyonu başarılı.")
            book_reservation_window.destroy()
        except IndexError:
            messagebox.showerror("Hata", "Lütfen bir kitap seçin.")

    book_reservation_window = tk.Toplevel(window)
    book_reservation_window.title("Kitap Rezervasyonu")
    book_reservation_window.geometry("400x450")

    books = load_data(BOOKS_FILE, lambda line: line.split(","))
    if not books:
        messagebox.showinfo("Bilgi", "Uygun kitap yok.")
        book_reservation_window.destroy()
        return

    tk.Label(book_reservation_window, text="Uygun Kitaplar:").pack(pady=5)
    listbox = tk.Listbox(book_reservation_window)
    for book in books:
        listbox.insert(tk.END, f"{book[0]} ({book[1]})")
    listbox.pack(pady=5)

    date_str = ""
    date_button = tk.Button(
        book_reservation_window, text="Tarih Seç", command=select_date
    )
    date_button.pack(pady=10)
    date_label = tk.Label(book_reservation_window, text="Seçilen Tarih: ")
    date_label.pack(pady=5)

    tk.Button(
        book_reservation_window,
        text="Rezervasyon Yap",
        command=lambda: reserve(date_str),
    ).pack(pady=10)


def table_reservation(window):
    def select_date():
        def on_date_selected():
            nonlocal date_str
            date_str = cal.get_date()
            date_label.config(text="Seçilen Tarih: " + date_str)
            top.destroy()

        top = tk.Toplevel(table_reservation_window)
        top.title("Tarih Seç")
        cal = Calendar(
            top,
            selectmode="day",
            year=datetime.date.today().year,
            month=datetime.date.today().month,
            day=datetime.date.today().day,
            mindate=datetime.date.today(),
            maxdate=datetime.date.today() + datetime.timedelta(days=14),
            date_pattern='dd.mm.yyyy'  # Tarih formatı burada belirlendi
        )
        cal.pack(pady=20)
        tk.Button(top, text="Onayla", command=on_date_selected).pack()

    def reserve(date_str):
        try:
            selected_index = listbox.curselection()[0]
            selected_table = tables[selected_index]
            start_time = start_time_entry.get()
            end_time = end_time_entry.get()
            if check_table_conflict(selected_table[0], date_str, start_time, end_time):
                messagebox.showerror(
                    "Hata", "Bu masa zaten belirtilen saat aralığında dolu!"
                )
                return
            try:
                start_hour, start_minute = map(int, start_time.split(":"))
                end_hour, end_minute = map(int, end_time.split(":"))
                if not (
                    0 <= start_hour <= 23
                    and 0 <= start_minute <= 59
                    and 0 <= end_hour <= 23
                    and 0 <= end_minute <= 59
                ):
                    raise ValueError
                if start_hour > end_hour or (
                    start_hour == end_hour and start_minute >= end_minute
                ):
                    raise ValueError
            except ValueError:
                messagebox.showerror(
                    "Hata",
                    "Geçersiz saat formatı veya aralığı. Lütfen HH:MM formatında girin ve başlangıç saatinin bitiş saatinden önce olduğundan emin olun.",
                )
                return
            reservation_date = datetime.datetime.strptime(date_str, "%d.%m.%Y").date()
            reservations = load_data(
                TABLE_RESERVATIONS_FILE, lambda line: line.split(",")
            )
            reservations.append(
                (logged_in_user, selected_table[0], str(reservation_date), start_time, end_time)
            )
            save_data(
                TABLE_RESERVATIONS_FILE, reservations, lambda res: ",".join(res)
            )
            messagebox.showinfo("Başarılı", "Masa rezervasyonu başarılı.")
            table_reservation_window.destroy()
        except IndexError:
            messagebox.showerror("Hata", "Lütfen bir masa seçin.")

    table_reservation_window = tk.Toplevel(window)
    table_reservation_window.title("Masa Rezervasyonu")
    table_reservation_window.geometry("400x500")

    tables = load_data(TABLES_FILE, lambda line: line.split(","))
    if not tables:
        messagebox.showinfo("Bilgi", "Uygun masa yok.")
        table_reservation_window.destroy()
        return

    tk.Label(table_reservation_window, text="Uygun Masalar:").pack(pady=5)
    listbox = tk.Listbox(table_reservation_window)
    for table in tables:
        listbox.insert(tk.END, f"Masa {table[0]} (Kapasite: {table[1]})")
    listbox.pack(pady=5)

    date_str = ""
    date_button = tk.Button(
        table_reservation_window, text="Tarih Seç", command=select_date
    )
    date_button.pack(pady=10)
    date_label = tk.Label(table_reservation_window, text="Seçilen Tarih: ")
    date_label.pack(pady=5)

    tk.Label(table_reservation_window, text="Başlangıç Saati (HH:MM):").pack(pady=5)
    start_time_entry = tk.Entry(table_reservation_window)
    start_time_entry.pack(pady=5)

    tk.Label(table_reservation_window, text="Bitiş Saati (HH:MM):").pack(pady=5)
    end_time_entry = tk.Entry(table_reservation_window)
    end_time_entry.pack(pady=5)

    tk.Button(
        table_reservation_window,
        text="Rezervasyon Yap",
        command=lambda: reserve(date_str),
    ).pack(pady=10)


def view_book_reservations(window):
    reservations = load_data(BOOK_RESERVATIONS_FILE, lambda line: line.split(","))
    user_reservations = [res for res in reservations if res[0] == logged_in_user]
    if not user_reservations:
        messagebox.showinfo("Bilgi", "Kitap rezervasyonunuz yok.")
        return

    view_reservations_window = tk.Toplevel(window)
    view_reservations_window.title("Kitap Rezervasyonları")

    tk.Label(view_reservations_window, text="Kitap Rezervasyonlarınız:").pack(pady=5)
    listbox = tk.Listbox(view_reservations_window)
    for res in user_reservations:
        listbox.insert(tk.END, f"Kitap: {res[1]}, Tarih: {res[2]}")
    listbox.pack(pady=5)

    def cancel_selected():
        selected = listbox.curselection()
        if selected:
            cancel_reservation(BOOK_RESERVATIONS_FILE, user_reservations[selected[0]])
            listbox.delete(selected[0])
            messagebox.showinfo("Başarılı", "Rezervasyon iptal edildi.")

    tk.Button(
        view_reservations_window, text="İptal Et", command=cancel_selected
    ).pack(pady=10)


def view_table_reservations(window):
    reservations = load_data(TABLE_RESERVATIONS_FILE, lambda line: line.split(","))
    user_reservations = [res for res in reservations if res[0] == logged_in_user]
    if not user_reservations:
        messagebox.showinfo("Bilgi", "Masa rezervasyonunuz yok.")
        return

    view_reservations_window = tk.Toplevel(window)
    view_reservations_window.title("Masa Rezervasyonları")

    tk.Label(view_reservations_window, text="Masa Rezervasyonlarınız:").pack(pady=5)
    listbox = tk.Listbox(view_reservations_window)
    for res in user_reservations:
        listbox.insert(
            tk.END, f"Masa: {res[1]}, Tarih: {res[2]}, Saat: {res[3]}-{res[4]}"
        )
    listbox.pack(pady=5)

    def cancel_selected():
        selected = listbox.curselection()
        if selected:
            cancel_reservation(TABLE_RESERVATIONS_FILE, user_reservations[selected[0]])
            listbox.delete(selected[0])
            messagebox.showinfo("Başarılı", "Rezervasyon iptal edildi.")

    tk.Button(
        view_reservations_window, text="İptal Et", command=cancel_selected
    ).pack(pady=10)


def book_menu(window):
    book_menu_window = tk.Toplevel(window)
    book_menu_window.title("Kitap İşlemleri")

    add_book_button = tk.Button(
        book_menu_window, text="Kitap Ekle", command=lambda: add_book(book_menu_window)
    )
    add_book_button.pack(pady=10)

    back_button = tk.Button(
        book_menu_window, text="Ana Menüye Dön", command=book_menu_window.destroy
    )
    back_button.pack(pady=10)


def table_menu(window):
    table_menu_window = tk.Toplevel(window)
    table_menu_window.title("Masa İşlemleri")

    add_table_button = tk.Button(
        table_menu_window,
        text="Masa Ekle",
        command=lambda: add_table(table_menu_window),
    )
    add_table_button.pack(pady=10)

    back_button = tk.Button(
        table_menu_window, text="Ana Menüye Dön", command=table_menu_window.destroy
    )
    back_button.pack(pady=10)


def reservation_menu(window):
    reservation_menu_window = tk.Toplevel(window)
    reservation_menu_window.title("Rezervasyon İşlemleri")

    book_reservation_button = tk.Button(
        reservation_menu_window,
        text="Kitap Rezervasyonu",
        command=lambda: book_reservation(reservation_menu_window),
    )
    book_reservation_button.pack(pady=5)

    table_reservation_button = tk.Button(
        reservation_menu_window,
        text="Masa Rezervasyonu",
        command=lambda: table_reservation(reservation_menu_window),
    )
    table_reservation_button.pack(pady=5)

    view_book_reservations_button = tk.Button(
        reservation_menu_window,
        text="Kitap Rezervasyonlarımı Görüntüle",
        command=lambda: view_book_reservations(reservation_menu_window),
    )
    view_book_reservations_button.pack(pady=5)

    view_table_reservations_button = tk.Button(
        reservation_menu_window,
        text="Masa Rezervasyonlarımı Görüntüle",
        command=lambda: view_table_reservations(reservation_menu_window),
    )
    view_table_reservations_button.pack(pady=5)

    back_button = tk.Button(
        reservation_menu_window,
        text="Ana Menüye Dön",
        command=reservation_menu_window.destroy,
    )
    back_button.pack(pady=5)


def main_menu(window):
    window.title("Kütüphane Rezervasyon Sistemi")
    window.geometry("300x400")
    window.resizable(False, False)

    if logged_in_user:
        tk.Button(
            window, text="Kitap İşlemleri", command=lambda: book_menu(window)
        ).pack(pady=10)
        tk.Button(
            window, text="Masa İşlemleri", command=lambda: table_menu(window)
        ).pack(pady=10)
        tk.Button(
            window, text="Rezervasyon", command=lambda: reservation_menu(window)
        ).pack(pady=10)
        tk.Button(window, text="Çıkış Yap", command=lambda: logout(window)).pack(
            pady=10
        )
    else:
        tk.Button(window, text="Kaydol", command=lambda: register_user(window)).pack(
            pady=10
        )
        tk.Button(window, text="Giriş Yap", command=lambda: login_user(window)).pack(
            pady=10
        )
        tk.Button(window, text="Admin Girişi", command=lambda: admin_login(window)).pack(
            pady=10
        )
        tk.Button(window, text="Çıkış", command=window.destroy).pack(pady=10)


def logout(window):
    global logged_in_user
    logged_in_user = None
    window.destroy()
    main_menu(tk.Tk())


if __name__ == "__main__":
    initialize_files()
    logged_in_user = None
    root = tk.Tk()
    main_menu(root)
    root.mainloop()