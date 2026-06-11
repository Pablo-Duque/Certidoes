import csv
from pathlib import Path

import pandas as pd

from certidoes import Bot


def main():
    path = Path.home() / "Downloads" / "Teste.xlsx"
    df = pd.read_excel(path, usecols=[4, 5, 16])
    df.columns = ["name", "cnpj", "type"]
    df = df[df["type"] == "Pessoa Jurídica"]
    map = df.set_index("cnpj")["name"].to_dict()

    keys = ["cadastro", "simples", "cnd", "fgts", "cndt"]
    labels = {
        "cadastro": "Situação Cadastral",
        "simples": "Simples",
        "cnd": "CND",
        "fgts": "FGTS",
        "cndt": "CNDT",
    }
    header = [["CNPJ"], ["Nome"]]
    result = []
    token_cnpj = set()
    for key in keys:
        header.append(labels[key])

    bot = Bot(keys)

    for cnpj, name in map.items():
        clean_cnpj = "".join(filter(str.isdigit, cnpj))
        token = clean_cnpj[:8]

        # se for a matriz armazena o token, pois nao quero rodar de novo 
        # o foco é verificar apenas as matrizes para não verificar linhas
        # desnecessarias
        if token not in token_cnpj and token[11] == 1:
            token_cnpj.add(token)
            response = bot.search(cnpj)
            result.append(
                [
                    cnpj,
                    name,
                    response["cadastro"][0],
                    response["simples"][0],
                    response["cnd"][0],
                    response["fgts"][0],
                    response["cndt"][0],
                ]
            )

    with open(
        "Resultado_consulta.csv", mode="w", newline="", encoding="utf-8-sig"
    ) as file:
        writer = csv.writer(file, delimiter=";")
        writer.writerow(header)
        writer.writerows(result.items())


if __name__ == "__main__":
    main()
