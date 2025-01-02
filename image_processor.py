import os
from pathlib import Path
from typing import Dict, Optional, Callable
from PIL import Image
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures
import time
import logging
import argparse

class GuiLoggingHandler(logging.Handler):
    def __init__(self, update_func):
        super().__init__()
        self.update_func = update_func

    def emit(self, record):
        log_message = self.format(record)
        # Lista completa de mensagens relevantes para exibir
        relevant_phrases = [
            "Iniciando mapeamento",
            "Total de imagens encontradas",
            "Início do processamento",
            "Total de imagens a processar",
            "Processado:",
            "Processamento concluído",
            "Imagens processadas com sucesso",
            "Imagens que falharam",
            "Falha ao processar",
            "Processamento interrompido"
        ]
        
        if any(phrase in log_message for phrase in relevant_phrases):
            self.update_func(log_message)

class ImageProcessor:
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.supported_formats = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif', '.webp'}
        self.stop_flag = False
        self.success_count = 0
        self.failure_count = 0
        self.failed_images = []
        self.quality = 85

    def find_image_files(self, input_folder: str):
        """Mapeia todas as imagens e suas localizações."""
        self.logger.info(f"Iniciando mapeamento de imagens no diretório: {input_folder}")
        images = {}
        for root, _, files in os.walk(input_folder):
            for file in files:
                if Path(file).suffix.lower() in self.supported_formats:
                    relative_path = Path(root).relative_to(input_folder)
                    if relative_path not in images:
                        images[relative_path] = []
                    images[relative_path].append(Path(root) / file)
        total_images = sum(len(files) for files in images.values())
        self.logger.info(f"Total de imagens encontradas: {total_images}")
        return images

    def process_images(self, input_folder: str, output_folder: str, width: int, slice_height: int, 
                      output_format: Optional[str], update_progress_callback: Callable, quality: int = 85):
        """
        Processa as imagens com a qualidade especificada.
        """
        self.quality = quality
        images_map = self.find_image_files(input_folder)
        total_images = sum(len(files) for files in images_map.values())

        if total_images == 0:
            self.logger.info("Nenhuma imagem encontrada para processar.")
            return

        os.makedirs(output_folder, exist_ok=True)

        processed_count = 0
        start_time = time.time()

        self.logger.info(f"Início do processamento: {time.strftime('%H:%M:%S', time.localtime(start_time))}")
        self.logger.info(f"Total de imagens a processar: {total_images}")

        for relative_path, files in images_map.items():
            if self.stop_flag:
                self.logger.info("Processamento interrompido pelo usuário.")
                break

            output_path = Path(output_folder) / relative_path
            output_path.mkdir(parents=True, exist_ok=True)

            with ThreadPoolExecutor(max_workers=4) as executor:
                # Lista para armazenar as imagens processadas
                processed_images = []
                
                for file in files:
                    if self.stop_flag:
                        break
                        
                    try:
                        with Image.open(file) as img:
                            if self.stop_flag:
                                break
                            resized_img = img.resize(
                                (width, int((width / img.width) * img.height)),
                                Image.Resampling.LANCZOS
                            )
                            processed_images.append(resized_img)
                    except Exception as e:
                        self.failed_images.append(file)
                        self.logger.error(f"Falha ao processar a imagem {file}: {e}")
                        self.failure_count += 1
                        continue

                if slice_height > 0 and not self.stop_flag and processed_images:
                    # Calcula altura total
                    total_height = sum(img.height for img in processed_images)
                    strip = Image.new('RGB', (width, total_height))

                    current_height = 0
                    for img in processed_images:
                        if self.stop_flag:
                            break
                        strip.paste(img, (0, current_height))
                        current_height += img.height

                    # Fatiamento
                    for i in range(0, strip.height, slice_height):
                        if self.stop_flag:
                            break
                        box = (0, i, strip.width, min(i + slice_height, strip.height))
                        slice_image = strip.crop(box)
                        slice_file = output_path / f"slice_{i // slice_height}.{files[0].suffix.lower()}"
                        self._save_image(slice_image, slice_file, output_format)
                else:
                    # Salvar imagens individuais
                    for img, file in zip(processed_images, files):
                        if self.stop_flag:
                            break
                        if img:
                            self._save_image(img, output_path / file.name, output_format)

            processed_count += len(files)
            if processed_count % 5 == 0 or processed_count == total_images:
                elapsed_time = time.time() - start_time
                self.logger.info(f"Processado: {processed_count}/{total_images} imagens - Tempo decorrido: {elapsed_time:.1f}s")
                progress_value = (processed_count / total_images) * 100
                update_progress_callback(progress_value)

        end_time = time.time()
        processing_time = end_time - start_time

        if self.stop_flag:
            self.logger.info("Processamento interrompido pelo usuário")
        else:
            self.logger.info(f"Processamento concluído em {processing_time:.1f} segundos")
            self.logger.info(f"Imagens processadas com sucesso: {self.success_count}")
            self.logger.info(f"Imagens que falharam: {self.failure_count}")

    def _save_image(self, image: Image.Image, file_path: Path, output_format: Optional[str] = None):
        """Salva a imagem processada com as configurações especificadas."""
        format_to_save = output_format.upper() if output_format else image.format
        
        try:
            if format_to_save == 'JPEG':
                image = image.convert('RGB')
                image.save(file_path, format_to_save, quality=self.quality, optimize=True, progressive=True)
            elif format_to_save == 'PNG':
                compress_level = max(0, min(9, int(9 - (self.quality / 11.111))))
                image.save(file_path, format_to_save, optimize=True, compress_level=compress_level)
            elif format_to_save == 'WEBP':
                image.save(file_path, format_to_save, quality=self.quality, optimize=True)
            else:
                image.save(file_path, format_to_save)

            self.logger.info(f"Imagem salva com qualidade {self.quality}%: {file_path}")
            self.success_count += 1
        except Exception as e:
            self.logger.error(f"Falha ao salvar imagem {file_path}: {e}")
            self.failure_count += 1

    def stop_processing(self):
        """Interrompe o processamento de imagens."""
        self.stop_flag = True
        self.logger.info("Solicitação de interrupção recebida")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Processador de Imagens")
    parser.add_argument("input_dir", type=str, help="Diretório de entrada com imagens")
    parser.add_argument("output_dir", type=str, help="Diretório de saída para imagens processadas")
    parser.add_argument("--width", type=int, default=800, help="Largura-alvo para redimensionamento das imagens")
    parser.add_argument("--slice_height", type=int, default=600, help="Altura de fatiamento das imagens")
    parser.add_argument("--output_format", type=str, choices=['jpeg', 'png', 'webp'], help="Formato de saída das imagens")
    parser.add_argument("--quality", type=int, default=85, help="Qualidade da imagem (1-100)")

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    processor = ImageProcessor()
    
    def dummy_progress_callback(value):
        print(f"Progresso: {value:.1f}%")

    processor.process_images(
        args.input_dir,
        args.output_dir,
        args.width,
        args.slice_height,
        args.output_format,
        dummy_progress_callback,
        quality=args.quality
    )
