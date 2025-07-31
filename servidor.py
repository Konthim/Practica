from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import sqlite3
import hashlib
import re

def validar_rut_chileno(rut):
    rut = rut.replace('.', '').replace('-', '').upper()
    if len(rut) < 8 or len(rut) > 9:
        return False
    numero = rut[:-1]
    dv = rut[-1]
    if not numero.isdigit():
        return False
    suma = 0
    multiplicador = 2
    for digito in reversed(numero):
        suma += int(digito) * multiplicador
        multiplicador += 1
        if multiplicador > 7:
            multiplicador = 2
    resto = suma % 11
    dv_calculado = 11 - resto
    if dv_calculado == 11:
        dv_calculado = '0'
    elif dv_calculado == 10:
        dv_calculado = 'K'
    else:
        dv_calculado = str(dv_calculado)
    return dv == dv_calculado

def init_db():
    conn = sqlite3.connect('usuarios.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            rut TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if '?id=' in self.path:
            user_id = self.path.split('?id=')[1]
            self.show_edit_form(user_id)
            return
            
        conn = sqlite3.connect('usuarios.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, nombre, rut, fecha_registro FROM usuarios ORDER BY id DESC')
        usuarios = cursor.fetchall()
        conn.close()
        
        usuarios_html = ""
        if usuarios:
            for usuario in usuarios:
                usuarios_html += f'''
                <tr class="user-row" data-nombre="{usuario[1].lower()}" data-rut="{usuario[2].lower()}">
                    <td>{usuario[0]}</td>
                    <td>{usuario[1]}</td>
                    <td>{usuario[2]}</td>
                    <td>{usuario[3]}</td>
                    <td>
                        <a href="/edit?id={usuario[0]}" class="edit-btn">Editar</a>
                        <form method="POST" style="display: inline;">
                            <input type="hidden" name="action" value="delete">
                            <input type="hidden" name="user_id" value="{usuario[0]}">
                            <button type="submit" class="delete-btn" onclick="return confirm('¿Estás seguro de eliminar este usuario?')">Eliminar</button>
                        </form>
                    </td>
                </tr>'''
        else:
            usuarios_html = '<tr><td colspan="5" style="text-align: center; color: #666;">No hay usuarios registrados</td></tr>'
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Sistema de Acceso</title>
    <style>
        :root {{
            --bg-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --container-bg: white;
            --text-color: #333;
            --text-secondary: #555;
            --border-color: #e1e5e9;
            --hover-bg: #f8f9fa;
            --input-bg: white;
        }}
        
        [data-theme="dark"] {{
            --bg-gradient: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
            --container-bg: #2c3e50;
            --text-color: #ecf0f1;
            --text-secondary: #bdc3c7;
            --border-color: #34495e;
            --hover-bg: #34495e;
            --input-bg: #34495e;
        }}
        
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: var(--bg-gradient); min-height: 100vh; padding: 20px; transition: all 0.3s ease; }}
        .container {{ background: var(--container-bg); padding: 40px; border-radius: 15px; box-shadow: 0 20px 40px rgba(0,0,0,0.1); width: 100%; max-width: 1200px; margin: 0 auto; transition: all 0.3s ease; }}
        .header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; }}
        h1, h2 {{ text-align: center; color: var(--text-color); margin-bottom: 30px; font-weight: 300; }}
        .theme-toggle {{ background: linear-gradient(135deg, #f39c12 0%, #e67e22 100%); color: white; padding: 10px 20px; border: none; border-radius: 8px; cursor: pointer; font-size: 14px; }}
        .search-container {{ margin-bottom: 20px; }}
        .search-input {{ width: 100%; max-width: 400px; padding: 12px 15px; border: 2px solid var(--border-color); border-radius: 8px; font-size: 16px; background: var(--input-bg); color: var(--text-color); }}
        .form-row {{ display: flex; gap: 20px; align-items: end; margin-bottom: 40px; }}
        .form-group {{ flex: 1; }}
        label {{ display: block; margin-bottom: 8px; color: var(--text-secondary); font-weight: 500; }}
        input {{ width: 100%; padding: 12px 15px; border: 2px solid var(--border-color); border-radius: 8px; font-size: 16px; transition: border-color 0.3s; background: var(--input-bg); color: var(--text-color); }}
        input:focus {{ outline: none; border-color: #667eea; }}
        button {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 12px 30px; border: none; border-radius: 8px; font-size: 16px; cursor: pointer; transition: transform 0.2s; }}
        button:hover {{ transform: translateY(-2px); }}
        .delete-btn {{ background: linear-gradient(135deg, #dc3545 0%, #c82333 100%); padding: 8px 16px; font-size: 14px; }}
        .edit-btn {{ background: linear-gradient(135deg, #28a745 0%, #20c997 100%); color: white; padding: 8px 16px; font-size: 14px; text-decoration: none; border-radius: 8px; margin-right: 10px; display: inline-block; }}
        .users-table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        .users-table th, .users-table td {{ padding: 12px; text-align: left; border-bottom: 1px solid var(--border-color); color: var(--text-color); }}
        .users-table th {{ background: var(--hover-bg); font-weight: 600; }}
        .users-table tr:hover {{ background: var(--hover-bg); }}
        .section {{ margin-bottom: 40px; }}
        hr {{ border: none; height: 2px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); margin: 40px 0; border-radius: 2px; }}
        .validation-info {{ font-size: 12px; margin-top: 5px; }}
        .valid {{ color: #28a745; }}
        .invalid {{ color: #dc3545; }}
        .hidden {{ display: none; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Sistema de Acceso</h1>
            <button class="theme-toggle" onclick="toggleTheme()">🌙 Modo Oscuro</button>
        </div>
        
        <div class="section">
            <form method="POST">
                <input type="hidden" name="action" value="register">
                <div class="form-row">
                    <div class="form-group">
                        <label for="nombre">Nombre</label>
                        <input type="text" id="nombre" name="nombre" required>
                    </div>
                    <div class="form-group">
                        <label for="rut">RUT Chileno (ej: 12345678-9)</label>
                        <input type="text" id="rut" name="rut" placeholder="12345678-9" maxlength="10" required>
                        <div id="rut-validation" class="validation-info"></div>
                    </div>
                    <div class="form-group">
                        <label for="password">Contraseña (mín. 4 caracteres, 1 número)</label>
                        <input type="password" id="password" name="password" minlength="4" required>
                        <div id="password-validation" class="validation-info"></div>
                    </div>
                    <div class="form-group">
                        <button type="submit">Registrar</button>
                    </div>
                </div>
            </form>
        </div>
        
        <hr>
        
        <div class="section">
            <h2>Usuarios Registrados</h2>
            <div class="search-container">
                <input type="text" id="search" class="search-input" placeholder="🔍 Buscar por nombre o RUT...">
            </div>
            <table class="users-table">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Nombre</th>
                        <th>RUT</th>
                        <th>Fecha Registro</th>
                        <th>Acciones</th>
                    </tr>
                </thead>
                <tbody id="users-tbody">
                    {usuarios_html}
                </tbody>
            </table>
        </div>
    </div>
    <script>
        // Modo oscuro
        function toggleTheme() {{
            const body = document.body;
            const button = document.querySelector('.theme-toggle');
            
            if (body.getAttribute('data-theme') === 'dark') {{
                body.removeAttribute('data-theme');
                button.innerHTML = '🌙 Modo Oscuro';
                localStorage.setItem('theme', 'light');
            }} else {{
                body.setAttribute('data-theme', 'dark');
                button.innerHTML = '☀️ Modo Claro';
                localStorage.setItem('theme', 'dark');
            }}
        }}
        
        // Cargar tema guardado
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme === 'dark') {{
            document.body.setAttribute('data-theme', 'dark');
            document.querySelector('.theme-toggle').innerHTML = '☀️ Modo Claro';
        }}
        
        // Buscador
        document.getElementById('search').addEventListener('input', function() {{
            const searchTerm = this.value.toLowerCase();
            const rows = document.querySelectorAll('.user-row');
            
            rows.forEach(row => {{
                const nombre = row.getAttribute('data-nombre');
                const rut = row.getAttribute('data-rut');
                
                if (nombre.includes(searchTerm) || rut.includes(searchTerm)) {{
                    row.style.display = '';
                }} else {{
                    row.style.display = 'none';
                }}
            }});
        }});
        
        // Validaciones
        document.getElementById('password').addEventListener('input', function() {{
            const password = this.value;
            const validation = document.getElementById('password-validation');
            
            let messages = [];
            
            if (password.length >= 4) {{
                messages.push('<span class="valid">✓ Al menos 4 caracteres</span>');
            }} else {{
                messages.push('<span class="invalid">✗ Necesita al menos 4 caracteres</span>');
            }}
            
            if (/\\d/.test(password)) {{
                messages.push('<span class="valid">✓ Contiene al menos un número</span>');
            }} else {{
                messages.push('<span class="invalid">✗ Necesita al menos un número</span>');
            }}
            
            validation.innerHTML = messages.join('<br>');
        }});
        
        document.getElementById('rut').addEventListener('input', function() {{
            const rut = this.value;
            const validation = document.getElementById('rut-validation');
            
            if (rut.length >= 8) {{
                const rutClean = rut.replace(/\\./g, '').replace(/-/g, '').toUpperCase();
                if (rutClean.length >= 8 && rutClean.length <= 9) {{
                    const numero = rutClean.slice(0, -1);
                    const dv = rutClean.slice(-1);
                    
                    if (/^\\d+$/.test(numero)) {{
                        let suma = 0;
                        let multiplicador = 2;
                        
                        for (let i = numero.length - 1; i >= 0; i--) {{
                            suma += parseInt(numero[i]) * multiplicador;
                            multiplicador++;
                            if (multiplicador > 7) multiplicador = 2;
                        }}
                        
                        const resto = suma % 11;
                        let dvCalculado = 11 - resto;
                        
                        if (dvCalculado === 11) dvCalculado = '0';
                        else if (dvCalculado === 10) dvCalculado = 'K';
                        else dvCalculado = dvCalculado.toString();
                        
                        if (dv === dvCalculado) {{
                            validation.innerHTML = '<span class="valid">✓ RUT válido</span>';
                        }} else {{
                            validation.innerHTML = '<span class="invalid">✗ RUT no válido</span>';
                        }}
                    }} else {{
                        validation.innerHTML = '<span class="invalid">✗ RUT no válido</span>';
                    }}
                }} else {{
                    validation.innerHTML = '<span class="invalid">✗ RUT no válido</span>';
                }}
            }} else {{
                validation.innerHTML = '<span class="invalid">✗ RUT incompleto</span>';
            }}
        }});
    </script>
</body>
</html>'''
        self.wfile.write(html.encode())
    
    def show_edit_form(self, user_id):
        conn = sqlite3.connect('usuarios.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, nombre, rut FROM usuarios WHERE id = ?', (user_id,))
        usuario = cursor.fetchone()
        conn.close()
        
        if not usuario:
            self.send_response(404)
            self.end_headers()
            return
            
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Editar Usuario</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; }}
        .container {{ background: white; padding: 40px; border-radius: 15px; box-shadow: 0 20px 40px rgba(0,0,0,0.1); width: 100%; max-width: 600px; }}
        h1 {{ text-align: center; color: #333; margin-bottom: 30px; font-weight: 300; }}
        .form-group {{ margin-bottom: 20px; }}
        label {{ display: block; margin-bottom: 8px; color: #555; font-weight: 500; }}
        input {{ width: 100%; padding: 12px 15px; border: 2px solid #e1e5e9; border-radius: 8px; font-size: 16px; transition: border-color 0.3s; }}
        input:focus {{ outline: none; border-color: #667eea; }}
        button {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 12px 30px; border: none; border-radius: 8px; font-size: 16px; cursor: pointer; transition: transform 0.2s; margin-right: 10px; }}
        button:hover {{ transform: translateY(-2px); }}
        .cancel-btn {{ background: linear-gradient(135deg, #6c757d 0%, #5a6268 100%); }}
        .validation-info {{ font-size: 12px; margin-top: 5px; }}
        .valid {{ color: #28a745; }}
        .invalid {{ color: #dc3545; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Editar Usuario</h1>
        <form method="POST">
            <input type="hidden" name="action" value="update">
            <input type="hidden" name="user_id" value="{usuario[0]}">
            
            <div class="form-group">
                <label for="nombre">Nombre</label>
                <input type="text" id="nombre" name="nombre" value="{usuario[1]}" required>
            </div>
            
            <div class="form-group">
                <label for="rut">RUT Chileno</label>
                <input type="text" id="rut" name="rut" value="{usuario[2]}" maxlength="10" required>
            </div>
            
            <div class="form-group">
                <label for="password">Nueva Contraseña (mín. 4 caracteres, 1 número)</label>
                <input type="password" id="password" name="password" minlength="4" required>
                <div id="password-validation" class="validation-info"></div>
            </div>
            
            <button type="submit">Actualizar</button>
            <a href="/" class="cancel-btn" style="text-decoration: none; display: inline-block; padding: 12px 30px; border-radius: 8px; color: white;">Cancelar</a>
        </form>
    </div>
    <script>
        document.getElementById('password').addEventListener('input', function() {{
            const password = this.value;
            const validation = document.getElementById('password-validation');
            
            let messages = [];
            
            if (password.length >= 4) {{
                messages.push('<span class="valid">✓ Al menos 4 caracteres</span>');
            }} else {{
                messages.push('<span class="invalid">✗ Necesita al menos 4 caracteres</span>');
            }}
            
            if (/\\d/.test(password)) {{
                messages.push('<span class="valid">✓ Contiene al menos un número</span>');
            }} else {{
                messages.push('<span class="invalid">✗ Necesita al menos un número</span>');
            }}
            
            validation.innerHTML = messages.join('<br>');
        }});
    </script>
</body>
</html>'''
        self.wfile.write(html.encode())
    
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = urllib.parse.parse_qs(post_data.decode())
        
        action = data.get('action', [''])[0]
        
        if action == 'update':
            user_id = data.get('user_id', [''])[0]
            nombre = data.get('nombre', [''])[0]
            rut = data.get('rut', [''])[0]
            password = data.get('password', [''])[0]
            
            errors = []
            
            if len(password) < 4:
                errors.append('La contraseña debe tener al menos 4 caracteres')
            
            if not any(char.isdigit() for char in password):
                errors.append('La contraseña debe contener al menos un número')
            
            if not validar_rut_chileno(rut):
                self.send_response(302)
                self.send_header('Location', '/')
                self.end_headers()
                return
            
            if errors:
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                
                error_html = '<br>'.join(errors)
                error_page = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Error de Validación</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; }}
        .container {{ background: white; padding: 40px; border-radius: 15px; box-shadow: 0 20px 40px rgba(0,0,0,0.1); width: 100%; max-width: 600px; text-align: center; }}
        h1 {{ color: #dc3545; margin-bottom: 30px; }}
        .error {{ background: #f8d7da; color: #721c24; padding: 20px; border-radius: 8px; margin: 20px 0; border: 1px solid #f5c6cb; }}
        .back-btn {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 12px 30px; border: none; border-radius: 8px; font-size: 16px; cursor: pointer; text-decoration: none; display: inline-block; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>❌ Error de Validación</h1>
        <div class="error">
            {error_html}
        </div>
        <a href="/edit?id={user_id}" class="back-btn">Volver</a>
    </div>
</body>
</html>'''
                self.wfile.write(error_page.encode())
                return
            
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            conn = sqlite3.connect('usuarios.db')
            cursor = conn.cursor()
            cursor.execute('UPDATE usuarios SET nombre = ?, rut = ?, password_hash = ? WHERE id = ?',
                          (nombre, rut, password_hash, user_id))
            conn.commit()
            conn.close()
            
            self.send_response(302)
            self.send_header('Location', '/')
            self.end_headers()
            
        elif action == 'delete':
            user_id = data.get('user_id', [''])[0]
            conn = sqlite3.connect('usuarios.db')
            cursor = conn.cursor()
            cursor.execute('DELETE FROM usuarios WHERE id = ?', (user_id,))
            conn.commit()
            conn.close()
            
            self.send_response(302)
            self.send_header('Location', '/')
            self.end_headers()
            
        else:
            nombre = data.get('nombre', [''])[0]
            rut = data.get('rut', [''])[0]
            password = data.get('password', [''])[0]
            
            errors = []
            
            if len(password) < 4:
                errors.append('La contraseña debe tener al menos 4 caracteres')
            
            if not any(char.isdigit() for char in password):
                errors.append('La contraseña debe contener al menos un número')
            
            if not validar_rut_chileno(rut):
                self.send_response(302)
                self.send_header('Location', '/')
                self.end_headers()
                return
            
            if errors:
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                
                error_html = '<br>'.join(errors)
                error_page = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Error de Validación</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; }}
        .container {{ background: white; padding: 40px; border-radius: 15px; box-shadow: 0 20px 40px rgba(0,0,0,0.1); width: 100%; max-width: 600px; text-align: center; }}
        h1 {{ color: #dc3545; margin-bottom: 30px; }}
        .error {{ background: #f8d7da; color: #721c24; padding: 20px; border-radius: 8px; margin: 20px 0; border: 1px solid #f5c6cb; }}
        .back-btn {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 12px 30px; border: none; border-radius: 8px; font-size: 16px; cursor: pointer; text-decoration: none; display: inline-block; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>❌ Error de Validación</h1>
        <div class="error">
            {error_html}
        </div>
        <a href="/" class="back-btn">Volver</a>
    </div>
</body>
</html>'''
                self.wfile.write(error_page.encode())
                return
            
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            conn = sqlite3.connect('usuarios.db')
            cursor = conn.cursor()
            cursor.execute('INSERT INTO usuarios (nombre, rut, password_hash) VALUES (?, ?, ?)',
                          (nombre, rut, password_hash))
            conn.commit()
            conn.close()
            
            self.send_response(302)
            self.send_header('Location', '/')
            self.end_headers()

init_db()
print("Base de datos inicializada")

server = HTTPServer(('localhost', 8000), Handler)
print("Servidor corriendo en http://localhost:8000")
server.serve_forever()