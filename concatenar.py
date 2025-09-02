import os

# extensões que você quer juntar
EXTENSOES = {".hml", ".py", ".js", ".css"}

# pasta base (troque se precisar)
PASTA_BASE = "."

# arquivo final
ARQUIVO_SAIDA = "arquivos_concatenados.txt"


def concatenar_arquivos(pasta_base, arquivo_saida):
    with open(arquivo_saida, "w", encoding="utf-8") as saida:
        for root, _, files in os.walk(pasta_base):
            for file in files:
                _, ext = os.path.splitext(file)
                if ext.lower() in EXTENSOES:
                    caminho = os.path.join(root, file)

                    # escreve cabeçalho com caminho
                    saida.write(f"#{caminho}\n\n")

                    try:
                        with open(caminho, "r", encoding="utf-8", errors="ignore") as f:
                            conteudo = f.read()
                            saida.write(conteudo.strip())
                    except Exception as e:
                        saida.write(f"## Erro ao ler {caminho}: {e}")

                    # separador
                    saida.write("\n\n--------\n\n")


if __name__ == "__main__":
    concatenar_arquivos(PASTA_BASE, ARQUIVO_SAIDA)
    print(f"Concatenação concluída! Arquivo salvo em: {ARQUIVO_SAIDA}")
