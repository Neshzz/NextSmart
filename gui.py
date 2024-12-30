import tkinter as tk
from tkinter import ttk, filedialog
from PIL import Image, ImageTk
import threading
from pathlib import Path
import logging
from image_processor import ImageProcessor, GuiLoggingHandler
import os
import argparse

class ImageProcessorGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("NextSmart")
        self.root.geometry("500x400")
        
        self.set_icon()

        self.progress_var = tk.DoubleVar()
        self.status_var = tk.StringVar()
        self.is_processing = False
        
        self.setup_gui()
        
        # Agora, a função update_log já existe, então podemos configurar o logger aqui
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        log_handler = GuiLoggingHandler(self.update_log)
        log_formatter = logging.Formatter('%(message)s')  # Apenas a mensagem de log
        log_handler.setFormatter(log_formatter)
        self.logger.addHandler(log_handler)

    # Novo método para processar logs
    def update_log(self, message: str):
        """Atualiza o log exibido na interface gráfica."""
        # Exibe a mensagem do log na interface gráfica, na label de status
        self.status_var.set(message)
        self.root.update_idletasks()
        
    def set_icon(self):
        try:
            # Obtém o diretório do script atual
            script_dir = os.path.dirname(os.path.abspath(__file__))
            # Construímos o caminho absoluto para o ícone
            icon_path = os.path.join(script_dir, "Logo.ico")
            
            # Tente carregar um arquivo .ico ou .png
            img = Image.open(icon_path)  # ou "Logo.png"
            img = img.resize((32, 32))  # Redimensiona para 32x32 px
            photo = ImageTk.PhotoImage(img)
            self.root.iconphoto(True, photo)  # Define o ícone da janela
        except Exception as e:
            print(f"Erro ao carregar o ícone: {e}")
        
    def setup_gui(self):
        # Input Directory
        ttk.Label(self.root, text="Diretório de Entrada:").pack(pady=5)
        input_frame = ttk.Frame(self.root)
        input_frame.pack(fill='x', padx=20)
        
        self.input_entry = ttk.Entry(input_frame)
        self.input_entry.pack(side='left', fill='x', expand=True)
        ttk.Button(input_frame, text="Procurar", command=lambda: self.browse_directory(self.input_entry)).pack(side='right', padx=5)
        
        # Output Directory
        ttk.Label(self.root, text="Diretório de Saída:").pack(pady=5)
        output_frame = ttk.Frame(self.root)
        output_frame.pack(fill='x', padx=20)
        
        self.output_entry = ttk.Entry(output_frame)
        self.output_entry.pack(side='left', fill='x', expand=True)
        ttk.Button(output_frame, text="Procurar", command=lambda: self.browse_directory(self.output_entry)).pack(side='right', padx=5)
        
        # Settings Frame
        settings_frame = ttk.Frame(self.root)
        settings_frame.pack(fill='x', padx=20, pady=10)
        
        # Width
        width_frame = ttk.Frame(settings_frame)
        width_frame.pack(side='left', fill='x', expand=True, padx=5)
        ttk.Label(width_frame, text="Largura do Corte (px):").pack()
        self.width_var = tk.StringVar(value="800")
        ttk.Entry(width_frame, textvariable=self.width_var).pack(fill='x')
        
        # Height
        height_frame = ttk.Frame(settings_frame)
        height_frame.pack(side='right', fill='x', expand=True, padx=5)
        ttk.Label(height_frame, text="Altura do Corte (px):").pack()
        self.height_var = tk.StringVar(value="600")
        ttk.Entry(height_frame, textvariable=self.height_var).pack(fill='x')
        
        # Process Button
        self.process_button = ttk.Button(self.root, text="Confirmar", command=self.start_processing)
        self.process_button.pack(pady=20)
        
        # Progress Bar
        self.progress = ttk.Progressbar(self.root, variable=self.progress_var, maximum=100)
        self.progress.pack(fill='x', padx=20, pady=5)
        
        # Status Label
        self.status_label = ttk.Label(self.root, textvariable=self.status_var)
        self.status_label.pack(pady=5)
        
    def browse_directory(self, entry):
        directory = filedialog.askdirectory()
        if directory:
            entry.delete(0, tk.END)
            entry.insert(0, directory)
            
    def update_progress(self, value):
        self.progress_var.set(value)
        self.root.update_idletasks()
        
    def start_processing(self):
        if self.is_processing:
            return

        input_dir = self.input_entry.get()
        output_dir = self.output_entry.get()

        if not input_dir or not output_dir:
            self.status_var.set("Please select input and output directories")
            return

        try:
            width = int(self.width_var.get())
            height = int(self.height_var.get())
        except ValueError:
            self.status_var.set("Invalid width or height values")
            return

        self.is_processing = True
        self.process_button.config(state='disabled')
        self.status_var.set("Processing images...")

        def process():
            try:
                # Passando logger para o ImageProcessor
                processor = ImageProcessor(self.logger)
                processor.process_images(input_dir, output_dir, width, height)
                self.root.after(0, self.processing_complete)
            except Exception as e:
                self.root.after(0, lambda: self.processing_error(str(e)))

        threading.Thread(target=process, daemon=True).start()

        
    def processing_complete(self):
        self.is_processing = False
        self.process_button.config(state='normal')
        self.status_var.set("Processing complete")
        self.progress_var.set(100)
        
    def processing_error(self, error_message):
        self.is_processing = False
        self.process_button.config(state='normal')
        self.status_var.set(f"Error: {error_message}")
        
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = ImageProcessorGUI()
    app.run()