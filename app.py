from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Necesario para los mensajes flash

UPLOAD_FOLDER = './uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Ruta principal
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        files = request.files.getlist("files[]")
        for file in files:
            if file.filename:
                filename = secure_filename(file.filename)
                file.save(os.path.join(UPLOAD_FOLDER, filename))
        flash("Archivos subidos y organizados correctamente.", "success")
        return redirect(url_for("index"))

    # Mostrar archivos organizados por categorías
    organized_files = organize_files()
    return render_template("index.html", files=organized_files)


import re  # Para trabajar con expresiones regulares

def organize_files():
    # Categorías base
    categories = [
        "STP", "AIU_2", "AIU", "AUT", "HACE26", "HCE", "NEV", "NEV1",
        "NDE", "PROCMENOR", "AYD", "AYD1", "LAB", "LAB1", "AYD1",
        "HAD", "FMD1"
    ]
    
    # Crear un diccionario para organizar archivos
    organized = {category: [] for category in categories}
    organized["NO VA"] = []

    # Diccionario para patrones que aceptan números variables
    patterns = {
        "AIU_2": r"^AIU_\d+$",
        "HACE26": r"^HACE\d+$",
        "NEV1": r"^NEV\d+$",
        "AYD1": r"^AYD1\d+$",
        "LAB1": r"^LAB1\d+$",
        "FMD1": r"^FMD1\d+$",
    }

    # Clasificar archivos en categorías
    for file in os.listdir(UPLOAD_FOLDER):
        added = False

        # Buscar coincidencias exactas
        for category in categories:
            if file.startswith(category):
                organized[category].append(file)
                added = True
                break

        # Buscar coincidencias con patrones
        if not added:
            for category, pattern in patterns.items():
                if re.match(pattern, file):
                    organized[category].append(file)
                    added = True
                    break

        # Si no pertenece a ninguna categoría, enviarlo a "NO VA"
        if not added:
            organized["NO VA"].append(file)

    # Ordenar categorías específicas
    organized["AYD1"] = sorted(organized["AYD1"])
    organized["LAB1"] = sorted(organized["LAB1"])

    return organized



# Ruta para eliminar un archivo
@app.route("/delete/<category>/<filename>", methods=["POST"])
def delete_file(category, filename):
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        flash(f"Archivo '{filename}' eliminado correctamente.", "success")
    else:
        flash(f"Archivo '{filename}' no encontrado.", "danger")
    return redirect(url_for("index"))


# Ruta para renombrar un archivo
@app.route("/rename/<category>/<filename>", methods=["POST"])
def rename_file(category, filename):
    new_name = request.form.get("new_name")
    if not new_name:
        flash("El nuevo nombre no puede estar vacío.", "danger")
        return redirect(url_for("index"))

    old_filepath = os.path.join(UPLOAD_FOLDER, filename)
    new_filepath = os.path.join(UPLOAD_FOLDER, secure_filename(new_name))

    if os.path.exists(old_filepath):
        os.rename(old_filepath, new_filepath)
        flash(f"Archivo '{filename}' renombrado a '{new_name}'.", "success")
    else:
        flash(f"Archivo '{filename}' no encontrado.", "danger")
    return redirect(url_for("index"))


# Ruta para descargar archivos (opcional)
from flask import send_file, send_from_directory
import zipfile
from PyPDF2 import PdfMerger

@app.route('/download_zip')
def download_zip():
    zip_filename = "organized_files.zip"
    zip_filepath = os.path.join(UPLOAD_FOLDER, zip_filename)

    # Crear el archivo ZIP
    with zipfile.ZipFile(zip_filepath, 'w') as zipf:
        for root, _, files in os.walk(UPLOAD_FOLDER):
            for file in files:
                filepath = os.path.join(root, file)
                zipf.write(filepath, os.path.relpath(filepath, UPLOAD_FOLDER))

    return send_file(zip_filepath, as_attachment=True)

from flask import request, jsonify

@app.route('/download_combined_pdf', methods=['POST'])
def download_combined_pdf():
    # Obtener el orden de los archivos desde el front-end
    data = request.json
    ordered_files = data.get('ordered_files', [])

    combined_pdf = os.path.join(UPLOAD_FOLDER, "combined_output.pdf")
    merger = PdfMerger()

    # Agregar los archivos al combinador en el orden recibido
    for filename in ordered_files:
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        if os.path.exists(filepath) and filepath.endswith('.pdf'):
            merger.append(filepath)

    # Guardar el archivo combinado
    merger.write(combined_pdf)
    merger.close()

    return send_file(combined_pdf, as_attachment=True)


from flask import send_file, abort

@app.route("/view_file/<category>/<filename>")
def view_file(category, filename):
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    try:
        # Validar si el archivo existe
        if os.path.exists(file_path):
            # Devolver el archivo para visualizarlo
            return send_file(file_path)
        else:
            abort(404)  # Archivo no encontrado
    except Exception as e:
        print(f"Error al abrir el archivo {filename}: {e}")
        abort(500)  # Error interno del servidor


if __name__ == "__main__":
    app.run(debug=True)
