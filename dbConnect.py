import pymysql
from tkinter import messagebox


def connect_to_dbusers():
    try:
        connection = pymysql.connect(
            host='localhost',
            database='dbusers',
            user='root',
            password=''
        )
        return connection
    except pymysql.MySQLError as e:
        messagebox.showerror("Database Error", f"Error connecting to database: {e}")
        return None

def connect_to_dbanime():
    try:
        connection = pymysql.connect(
            host='localhost',
            database='dbanime',
            user='root',
            password=''
        )
        return connection
    except pymysql.MySQLError as e:
        messagebox.showerror("Database Error", f"Error connecting to database: {e}")
        return None