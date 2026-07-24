import flet as ft
from fpdf import FPDF

class PDF(FPDF):
    def header(self):
        # Nota: FPDF tiene limitaciones con emojis a color. 
        # Incluso con fuentes Unicode, los emojis suelen verse en blanco y negro o como cuadrados.
        # Por eso en el proyecto principal (pdf_generator.py) removimos los emojis del PDF.
        self.set_font("Helvetica", "B", 16)

def generar_pdf(e):
    pdf = PDF()
    pdf.add_page()
    
    # Escribir texto (recomendado sin emojis para máxima compatibilidad en FPDF)
    pdf.cell(200, 10, txt="Hola desde Flet! (Prueba de PDF)", ln=True, align="C")
    pdf.ln(10)
    pdf.cell(200, 10, txt="El archivo se ha generado correctamente en la carpeta del proyecto.", ln=True, align="C")
    
    # Guardar el archivo PDF en disco
    pdf.output("test_flet.pdf")
    
    # ✅ CORREGIDO para Flet 0.86+: cambiar el texto del botón
    e.control.content.value = "¡PDF Creado Exitosamente!"
    e.control.update()

def main(page: ft.Page):
    page.title = "Exportar a PDF"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.VerticalAlignment.CENTER
    
    page.add(
        # ✅ CORREGIDO para Flet 0.