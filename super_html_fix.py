import os
import re

# Mapeo de caracteres especiales a sus entidades HTML
CHAR_MAP = {
    'á': '&aacute;', 'é': '&eacute;', 'í': '&iacute;', 'ó': '&oacute;', 'ú': '&uacute;',
    'Á': '&Aacute;', 'É': '&Eacute;', 'Í': '&Iacute;', 'Ó': '&Oacute;', 'Ú': '&Uacute;',
    'ñ': '&ntilde;', 'Ñ': '&Ntilde;',
    'ü': '&uuml;', 'Ü': '&Uuml;',
    '¿': '&iquest;', '¡': '&iexcl;',
    '€': '&euro;', # Símbolo del euro, si lo usas
    'º': '&ordm;', 'ª': '&ordf;', # Ordinales masculinos/femeninos
}

def convert_to_html_entities(text):
    for char, entity in CHAR_MAP.items():
        text = text.replace(char, entity)
    return text

def read_file_with_fallback(filepath):
    """Intenta leer un archivo con UTF-8, luego Windows-1252."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read(), 'utf-8'
    except UnicodeDecodeError:
        try:
            with open(filepath, 'r', encoding='cp1252') as f: # cp1252 es muy común para Latín-1 en Windows/Mac
                return f.read(), 'cp1252'
        except Exception as e:
            print(f"Error al leer '{filepath}' con UTF-8 o cp1252: {e}")
            return None, None

def process_html_files(directory):
    if not os.path.isdir(directory):
        print(f"Error: El directorio '{directory}' no existe.")
        return

    for root, _, files in os.walk(directory): # Recorre todas las subcarpetas
        for filename in files:
            if filename.endswith(".html"):
                filepath = os.path.join(root, filename)
                print(f"Procesando: {filepath}")
                
                content, detected_encoding = read_file_with_fallback(filepath)
                if content is None:
                    continue # Saltar si no se pudo leer

                print(f"  Codificación detectada para '{filename}': {detected_encoding}")

                # 1. Convertir caracteres especiales a entidades HTML *antes* de modificar la estructura
                # Esto asegura que los caracteres especiales se manejen primero.
                content = convert_to_html_entities(content)

                # 2. Asegurar la estructura HTML básica y la meta charset
                has_doctype = re.search(r'<!DOCTYPE html>', content, re.IGNORECASE)
                has_html_tag = re.search(r'<html.*?>', content, re.IGNORECASE)
                has_head_tag = re.search(r'<head.*?>', content, re.IGNORECASE)
                has_body_tag = re.search(r'<body.*?>', content, re.IGNORECASE)
                has_meta_charset = re.search(r'<meta charset=["\']?utf-8["\']?>', content, re.IGNORECASE)

                new_meta_tag = '    <meta charset="UTF-8">' # Con indentación

                # Lógica para insertar <head> y meta charset
                if not has_head_tag:
                    if has_html_tag:
                        # Insertar <head> y meta charset después de <html>
                        content = re.sub(r'(<html.*?>)', r'\1\n<head>\n' + new_meta_tag + '\n</head>', content, flags=re.IGNORECASE, count=1)
                        print(f"  Añadida sección <head> y meta charset a '{filename}'.")
                    elif has_body_tag:
                        # Insertar <head> y meta charset antes de <body>
                        content = re.sub(r'(<body.*?>)', r'<head>\n' + new_meta_tag + '\n</head>\n\1', content, flags=re.IGNORECASE, count=1)
                        print(f"  Añadida sección <head> y meta charset antes de <body> en '{filename}'.")
                    else:
                        # Caso FrontPage: Añadir estructura completa al inicio
                        content = f"""<!DOCTYPE html>
<html lang="es">
<head>
{new_meta_tag}
    <title>Documento sin Título</title> </head>
<body>
{content}
</body>
</html>"""
                        print(f"  Añadida estructura HTML completa y meta charset a '{filename}'.")
                elif not has_meta_charset:
                    # Si ya hay <head> pero no tiene meta charset UTF-8 o tiene otro
                    if re.search(r'<meta charset=.*?>', content, re.IGNORECASE):
                        content = re.sub(r'<meta charset=["\'][^"\']*["\']>', new_meta_tag, content, flags=re.IGNORECASE)
                        print(f"  Actualizada meta charset a UTF-8 en '{filename}'.")
                    else:
                        content = re.sub(r'(<head.*?>)', r'\1\n' + new_meta_tag, content, flags=re.IGNORECASE, count=1)
                        print(f"  Añadida meta charset a <head> en '{filename}'.")

                # Asegurar DOCTYPE y <html> si faltan
                if not has_doctype and not content.strip().startswith('<!DOCTYPE html>'):
                    content = '<!DOCTYPE html>\n' + content
                    print(f"  Añadido DOCTYPE a '{filename}'.")
                if not has_html_tag and not re.search(r'<html.*?>', content, re.IGNORECASE): # Re-check after potential additions
                    # Intentar insertar <html> después de DOCTYPE si DOCTYPE fue recién añadido
                    if content.strip().startswith('<!DOCTYPE html>'):
                        content = re.sub(r'(<!DOCTYPE html>)', r'\1\n<html lang="es">', content, flags=re.IGNORECASE, count=1)
                        print(f"  Añadido <html> después de DOCTYPE en '{filename}'.")
                    else: # Si no hay DOCTYPE ni HTML y no se añadió estructura completa
                        content = '<html lang="es">\n' + content
                        print(f"  Añadido <html> al inicio de '{filename}'.")

                # Asegurar que el <body> y </body></html> estén al final si se añadió estructura completa
                if not has_body_tag and not re.search(r'<body.*?>', content, re.IGNORECASE):
                    # Si se añadió la estructura completa, el body ya está
                    pass # Ya se manejó al añadir la estructura completa
                elif not re.search(r'</body>', content, re.IGNORECASE) and not re.search(r'</html>', content, re.IGNORECASE):
                    # Asegurarse de añadir cierres si no existen
                    if re.search(r'<body.*?>', content, re.IGNORECASE): # Si el body existe o se añadió
                        content += '\n</body>\n</html>'
                        print(f"  Añadidos cierres </body></html> a '{filename}'.")
                    elif re.search(r'<html.*?>', content, re.IGNORECASE): # Si solo existe HTML
                        content += '\n</html>'
                        print(f"  Añadido cierre </html> a '{filename}'.")

                # 3. Escribir el archivo de vuelta en UTF-8
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"  '{filename}' guardado en UTF-8 con entidades HTML y estructura estandarizada.")

                print("-" * 50) # Separador para la salida
                
                
# --- INSTRUCCIONES ---
# 1. HAZ UNA COPIA DE SEGURIDAD COMPLETA DE TU CARPETA 'testudinae' ANTES DE EJECUTAR ESTO. ¡IMPRESCINDIBLE!
#    Es la última vez que te lo pido, pero es crítico. Usa la copia de seguridad que se veía bien en local.
# 2. Reemplaza 'tu_ruta_a_la_carpeta_testudinae' con la ruta real a tu carpeta.
# 3. Guarda este código como un archivo Python (ej. 'super_html_fix.py').
# 4. Abre tu terminal (en macOS, "Terminal").
# 5. Navega a la carpeta donde guardaste 'super_html_fix.py' usando el comando 'cd'.
#    Ej: cd /Users/tu_usuario/mis_scripts
# 6. Ejecuta el script: python3 super_html_fix.py
# --------------------

# REEMPLAZA ESTA RUTA CON LA RUTA REAL A TU CARPETA 'testudinae'
# Ya que has puesto el script dentro de la carpeta 'testudinae', usa el punto '.'
process_html_files('.') # <--- ¡ASEGÚRATE DE QUE LA RUTA SEA CORRECTA!