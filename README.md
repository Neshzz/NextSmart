# NextSmart
NextSmart (Image Processor)

Instruções para Uso do Código NextSmart

# Requisitos:

Certifique-se de que os seguintes requisitos estão instalados no seu ambiente:

Python 3.x (preferencialmente a versão mais recente)
Bibliotecas Python:
tkinter (para a interface gráfica)
Pillow (para processamento de imagens)
concurrent.futures (já incluída no Python 3.x)
logging (já incluída no Python 3.x)

# Instalando Dependências:
Antes de rodar o código, instale as dependências necessárias com o seguinte comando:


Copie código:

pip install pillow
pip install tkinter

Cole no terminal e aperte Enter

# Rodando o Aplicativo com a Interface Gráfica (GUI)
Execute o script gui.py:

No terminal ou prompt de comando, navegue até o diretório onde os arquivos estão armazenados e execute o seguinte comando:

Copie código: python gui.py 
Cole no terminal e aperte Enter

# Configuração na Interface Gráfica:

Diretório de Entrada: Clique no botão "Procurar" e selecione o diretório onde as imagens a serem processadas estão localizadas.

Diretório de Saída: Clique no botão "Procurar" e selecione o diretório onde as imagens processadas serão salvas.

Largura do Corte (px): Defina a largura desejada para redimensionamento das imagens.

Altura do Corte (px): Defina a altura do corte para dividir as imagens processadas.

Iniciar o Processamento: Clique no botão "Confirmar" para começar o processo de redimensionamento e fatiamento das imagens. O progresso será exibido na barra de progresso.

Finalização: O processamento é concluído quando a barra de progresso chega a 100%, e você verá uma mensagem indicando o sucesso.

# Rodando o Código pela Linha de Comando:

Se você preferir rodar o código diretamente pela linha de comando, sem a interface gráfica, você pode usar o script image_processor.py.

Execute o script image_processor.py via terminal ou prompt de comando com a seguinte sintaxe:

Copie código:
python image_processor.py <input_dir> <output_dir> --width <width> --slice_height <height>

<input_dir>: O diretório onde as imagens estão armazenadas.

<output_dir>: O diretório onde as imagens processadas serão salvas.

--width <width>: A largura de corte para as imagens. O valor padrão é 800px.

--slice_height <height>: A altura de corte para fatiar as imagens. O valor padrão é 600px.

Exemplo:

Copie código:
python image_processor.py ./input ./output --width 1200 --slice_height 500

# Exemplos de Funcionamento:

Diretório de Entrada: /imagens_originais/
Diretório de Saída: /imagens_processadas/
Largura do Corte: 1200px
Altura do Corte: 500px

Após o comando ser executado, o script irá processar todas as imagens do diretório de entrada, redimensioná-las para a largura especificada e então cortá-las em pedaços com a altura especificada, salvando-as no diretório de saída.

# Como Funciona o Código:
GUI (Interface Gráfica):

O arquivo gui.py cria uma interface onde você pode selecionar os diretórios de entrada e saída, definir parâmetros de corte e acompanhar o progresso em tempo real.
Processamento de Imagens:

O arquivo image_processor.py contém a lógica para redimensionar e cortar as imagens. Ele suporta múltiplos formatos de imagem e usa threads para acelerar o processamento.
Logging:

O log do processo é exibido na interface gráfica ou no terminal, informando o progresso das operações.

# Problemas Comuns:

Erro ao abrir a imagem: Isso pode ocorrer se o formato da imagem não for suportado (os formatos suportados são .jpg, .jpeg, .png, .bmp, .tiff, .gif, .webp).
Erro no diretório de entrada/saída: Verifique se os diretórios foram selecionados corretamente.

Outros Detalhes Importantes:

Redimensionamento: O código mantém a proporção das imagens ao redimensioná-las para a largura especificada.

Fatiamento: Após a criação da tira de imagem, a imagem é dividida em "fatias" com a altura definida por você.


Se faltou explicação de algo ou ocorreu um erro diferente me avise
