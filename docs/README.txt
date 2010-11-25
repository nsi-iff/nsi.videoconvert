Arquitetura do serviço de conversão de vídeo

    O serviço de conversão de vídeo é composto de um webservice, dependente do
    SAM (Serviço de Armazenamento Massivo) e responsável por fazer a conversão de
    todos os vídeos que serão enviados para a Biblioteca Digital.

    Possui apenas um método:

        convert: recebe um vídeo devidamente codificado em base 64, guarda-o
            no SAM marcado para conversão. Retornar para o usuário um UID (chave)
            onde se encontrará o vídeo convertido.

    A conversão será feita por um script "slave" disponível no buildout do pacote.

