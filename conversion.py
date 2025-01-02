import os
import io
from PIL import Image, UnidentifiedImageError
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict

def convert_image(file_path, output_directory, output_format='jpeg'):
    try:
        # Abre a imagem com máxima resolução e sem limite de memória
        with Image.open(file_path) as original_img:
            # Converte para RGB, preservando o modo de cor original
            img = original_img.convert('RGB')

            # Cria o caminho para salvar a imagem convertida, mantendo a estrutura de diretórios
            relative_path = os.path.relpath(file_path, os.path.dirname(output_directory))
            output_file_path = os.path.join(
                output_directory, 
                os.path.splitext(relative_path)[0] + f'.{output_format}'
            )

            # Cria o diretório de saída se não existir
            os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

            # Configurações de salvamento flexíveis
            save_options = {
                'optimize': True,
                'quality': 95  # Alta qualidade
            }

            # Tratamento específico para diferentes formatos
            if output_format.lower() in ['jpeg', 'jpg']:
                # Suporte para imagens extremamente grandes
                img.save(output_file_path, 'JPEG', **save_options, progressive=True)
            elif output_format.lower() == 'webp':
                # Configuração específica para WebP
                save_options['method'] = 6  # Melhor compressão
                save_options['lossless'] = False
                img.save(output_file_path, 'WEBP', **save_options)
            elif output_format.lower() == 'png':
                # Otimização para PNG
                save_options['compress_level'] = 9
                img.save(output_file_path, 'PNG', **save_options)
            else:
                img.save(output_file_path, output_format.upper(), **save_options)
        
        return os.path.basename(file_path), True
    except Exception as e:
        print(f"Erro ao converter {file_path}: {e}")
        return os.path.basename(file_path), False

def convert_images(
    directory, 
    output_format='jpeg', 
    log_callback=None
):
    # Configurações para lidar com imagens muito grandes
    Image.MAX_IMAGE_PIXELS = None  # Remove o limite de pixels
    
    directory = directory.strip('"')

    if not os.path.exists(directory):
        if log_callback:
            log_callback(f"O diretório '{directory}' não existe.", "ERROR")
        return

    # Diretório de saída base
    output_base_directory = directory + "-converted"
    os.makedirs(output_base_directory, exist_ok=True)

    # Formatos de imagem suportados
    supported_formats = (
        '.jpeg', '.jpg', '.png', '.bmp', '.gif', 
        '.webp', '.tiff', '.tif', '.raw', '.heic'
    )

    image_count_by_extension = defaultdict(int)
    total_images_converted = 0
    total_files = 0
    failed_files = []

    # Contar total de arquivos suportados
    for root, _, files in os.walk(directory):
        total_files += len([f for f in files if f.lower().endswith(supported_formats)])

    if total_files == 0:
        if log_callback:
            log_callback("Nenhuma imagem foi encontrada no diretório.", "WARNING")
        return

    # Usar ThreadPoolExecutor com número de workers baseado no número de CPUs
    with ThreadPoolExecutor(max_workers=os.cpu_count() or 4) as executor:
        futures = []
        processed_files = 0

        # Percorrer todas as pastas e subpastas
        for root, _, files in os.walk(directory):
            for filename in files:
                if filename.lower().endswith(supported_formats):
                    file_path = os.path.join(root, filename)
                    futures.append(
                        executor.submit(
                            convert_image, 
                            file_path, 
                            output_base_directory, 
                            output_format
                        )
                    )

        # Processar resultados
        for future in futures:
            filename, success = future.result()
            processed_files += 1
            
            if success:
                image_count_by_extension[os.path.splitext(filename)[1].lower()] += 1
                total_images_converted += 1
            else:
                failed_files.append(filename)
            
            # Atualizar log de progresso
            if log_callback:
                log_callback(f"Progresso: {processed_files}/{total_files} imagens", "INFO")

    # Exibe o relatório final
    if log_callback:
        log_callback(f"Total de imagens convertidas: {total_images_converted}", "SUCCESS")
        log_callback("Quantidade por tipo de imagem:", "INFO")
        for ext, count in image_count_by_extension.items():
            log_callback(f"{ext}: {count}", "INFO")
        
        # Log de arquivos que falharam
        if failed_files:
            log_callback("Arquivos que falharam na conversão:", "WARNING")
            for file in failed_files:
                log_callback(file, "ERROR")

def display_supported_formats():
    # Formatos que podem ser escolhidos
    supported_formats = ['jpeg', 'jpg', 'png', 'webp']

    print("Escolha o formato para a conversão:")
    for idx, format_ in enumerate(supported_formats, 1):
        print(f"{idx} - {format_}")

    # Solicita a escolha do usuário
    choice = int(input("\nDigite o número do formato desejado: "))

    # Escolhe o formato baseado na escolha do usuário
    if 1 <= choice <= len(supported_formats):
        return supported_formats[choice - 1]
    else:
        print("Escolha inválida.")
        return None

if __name__ == "__main__":
    directory = input("Insira o diretório das imagens: ")
    output_format = display_supported_formats()
    if output_format:
        convert_images(directory, output_format)