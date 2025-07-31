import sqlite3
from datetime import datetime

def consultar_usuarios():
    try:
        conn = sqlite3.connect('usuarios.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, nombre, rut, fecha_registro FROM usuarios ORDER BY id DESC')
        usuarios = cursor.fetchall()
        
        if usuarios:
            print("=== USUARIOS REGISTRADOS ===")
            print("-" * 60)
            for usuario in usuarios:
                print(f"ID: {usuario[0]}")
                print(f"Nombre: {usuario[1]}")
                print(f"RUT: {usuario[2]}")
                print(f"Fecha: {usuario[3]}")
                print("-" * 60)
        else:
            print("No hay usuarios registrados")
            
        conn.close()
        
    except sqlite3.Error as e:
        print(f"Error al consultar la base de datos: {e}")

if __name__ == "__main__":
    consultar_usuarios()