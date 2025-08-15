import os
import re

# Mapeo de caracteres especiales a sus entidades HTML (puedes añadir más si encuentras otros)
CHAR_MAP = {
    'á': '&aacute;', 'é': '&eacute;', 'í': '&iacute;', 'ó': '&oacute;', 'ú': '&uacute;',
    'Á': '&Aacute;', 'É': '&Eacute;', 'Í': '&Iacute;', 'Ó': '&Oacute;', 'Ú': '&Uacute;',
    'ñ': '&ntilde;', 'Ñ': '&Ntilde;',
    'ü': '&uuml;', 'Ü': '&Uuml;',
    '¿': '&iquest;', '¡': '&iexcl;',
    # No añadimos '&' a '&amp;' aquí, ni '<' a '&lt;', etc., porque eso podría doble-codificar HTML existente.
    # Estas entidades básicas HTML deben tratarse de forma separada si hay problemas.
}

def convert_to_html_entities(text):
    for char, entity in CHAR_MAP.items():
        # Usamos replace. El orden importa para cosas como 'Á' antes de 'á' si fuera necesario, pero aquí no.
        text = text.replace(char, entity)
    return text

def process_html_files(directory):
    if not os.path.isdir(directory):
        print(f"Error: El directorio '{directory}' no existe.")
        return

    for root, _, files in os.walk(directory): # Recorre todas las subcarpetas
        for filename in files:
            if filename.endswith(".html"):
                filepath = os.path.join(root, filename)
                try:
                    # 1. Leer el archivo como UTF-8 (ya que VS Code dice que es UTF-8)
                    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                        content = f.read()

                    original_content = content # Guardamos el original para ver si se añade estructura

                    # 2. Convertir caracteres especiales a entidades HTML *antes* de modificar la estructura
                    # Esto asegura que los caracteres especiales se manejen primero.
                    content = convert_to_html_entities(content)

                    # 3. Añadir o asegurar la estructura HTML básica y la meta charset
                    # Buscamos patrones de HTML estándar para decidir si envolver o insertar
                    has_doctype = re.search(r'<!DOCTYPE html>', content, re.IGNORECASE)
                    has_html_tag = re.search(r'<html.*?>', content, re.IGNORECASE)
                    has_head_tag = re.search(r'<head.*?>', content, re.IGNORECASE)
                    has_body_tag = re.search(r'<body.*?>', content, re.IGNORECASE)
                    has_meta_charset = re.search(r'<meta charset=["\']?utf-8["\']?>', content, re.IGNORECASE)

                    new_meta_tag = '    <meta charset="UTF-8">' # Con indentación

                    # Si no hay <head> pero hay <html>
                    if has_html_tag and not has_head_tag:
                        content = re.sub(r'(<html.*?>)', r'\1\n<head>\n' + new_meta_tag + '\n</head>', content, flags=re.IGNORECASE, count=1)
                        print(f"'{filename}': Añadida sección <head> y meta charset.")
                    # Si no hay <head> ni <html> ni DOCTYPE (caso FrontPage inicial)
                    elif not has_html_tag and not has_doctype:
                        # Buscamos la primera línea del archivo para insertar antes de ella
                        # O simplemente anteponemos la estructura completa
                        content = f"""<!DOCTYPE html>
<html lang="es">
<head>
{new_meta_tag}
    <title>:: testudinae.com ::</title>
</head>
<body>
{content}
</body>
</html>"""
                        print(f"'{filename}': Añadida estructura HTML completa y meta charset.")
                    # Si hay <head> pero no tiene meta charset UTF-8 o tiene otro
                    elif has_head_tag and not has_meta_charset:
                        if re.search(r'<meta charset=.*?>', content, re.IGNORECASE):
                            content = re.sub(r'<meta charset=["\'][^"\']*["\']>', new_meta_tag, content, flags=re.IGNORECASE)
                            print(f"'{filename}': Actualizada meta charset a UTF-8.")
                        else:
                            content = re.sub(r'(<head.*?>)', r'\1\n' + new_meta_tag, content, flags=re.IGNORECASE, count=1)
                            print(f"'{filename}': Añadida meta charset a <head>.")

                    # Asegurarse de que el DOCTYPE y <html> estén al principio si no se añadieron ya
                    if not has_doctype and not content.strip().startswith('<!DOCTYPE html>'):
                         content = '<!DOCTYPE html>\n' + content
                         print(f"'{filename}': Añadido DOCTYPE.")
                    if not has_html_tag and not content.strip().startswith('<html'):
                        content = content.replace('<!DOCTYPE html>\n', '<!DOCTYPE html>\n<html lang="es">\n')
                        print(f"'{filename}': Añadido <html>.")

                    # Asegurarse de que el <body> y </body></html> estén al final si se añadió estructura
                    if has_html_tag and not has_body_tag:
                        # Si se agregó html pero no body, envolvemos el contenido restante en body
                        # Esto es una suposición; podría ser más complejo.
                        if not re.search(r'<body.*?>', content, re.IGNORECASE) and not re.search(r'</body>', content, re.IGNORECASE):
                             content = re.sub(r'(</head>.*)', r'\1\n<body>', content, flags=re.DOTALL) # Añadir <body> después de </head> y su contenido
                             content += '\n</body>\n</html>'
                             print(f"'{filename}': Añadido <body> y cierre de HTML.")
                    elif not re.search(r'</body>', content, re.IGNORECASE) and not re.search(r'</html>', content, re.IGNORECASE):
                         if "<body>" in content: # Solo si ya hemos insertado <body> o existía
                            content += '\n</body>\n</html>'
                            print(f"'{filename}': Añadidos cierres </body></html>.")


                    # 4. Escribir el archivo de vuelta en UTF-8
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"'{filename}' procesado y guardado con entidades HTML y estructura estandarizada.")

                except Exception as e:
                    print(f"Error procesando '{filename}': {e}")

# --- INSTRUCCIONES ---
# 1. HAZ UNA COPIA DE SEGURIDAD COMPLETA DE TU CARPETA 'testudinae' ANTES DE EJECUTAR ESTO. ¡IMPRESCINDIBLE!
# 2. Reemplaza 'tu_ruta_a_la_carpeta_testudinae' con la ruta real a tu carpeta.
#    Por ejemplo: '/Users/tu_usuario/Documents/GitHub/testudinae'
# 3. Guarda este código como un archivo Python (ej. 'full_html_fix.py').
# 4. Abre tu terminal (en macOS, "Terminal").
# 5. Navega a la carpeta donde guardaste 'full_html_fix.py' usando el comando 'cd':
#    Ej: cd /Users/tu_usuario/mis_scripts
# 6. Ejecuta el script: python full_html_fix.py
# --------------------

# REEMPLAZA ESTA RUTA CON LA RUTA REAL A TU CARPETA 'testudinae'
# Por ejemplo: process_html_files('/Users/alpelokanelo/Documents/GitHub/testudinae')
# Si el script está en la carpeta superior a testudinae: process_html_files('./testudinae')
# Si el script está dentro de testudinae: process_html_files('.')
process_html_files('.') #