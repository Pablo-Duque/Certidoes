import csv
from pathlib import Path

import pandas as pd

from certidoes import Bot


def main():
    path = Path.home() / "Downloads"
    df = pd.read_excel(path / "Teste.xlsx", sheet_name="Contratos", usecols=[4, 5])
    df.columns = ["name", "cnpj"]
    df = df[df["cnpj"].str.len() == 18]
    map = df.set_index("cnpj")["name"].to_dict()

    keys = ["cadastro", "simples", "cnd", "fgts", "cndt"]
    labels = {
        "cadastro": "Situação Cadastral",
        "simples": "Simples",
        "cnd": "CND",
        "fgts": "FGTS",
        "cndt": "CNDT",
    }

    header = ["Nome", "CNPJ"] + [labels[k] for k in keys]
    result = []
    token_cnpj = []

    bot = Bot(keys)
    i = 0

    for cnpj, name in map.items():
        i += 1
        if i == 4:
            break

        clean_cnpj = "".join(filter(str.isdigit, cnpj))
        token = clean_cnpj[:8]
        # se for a matriz armazena o token, pois nao quero rodar de novo 
        # o foco é verificar apenas as matrizes para não verificar linhas
        # desnecessarias

        if token not in token_cnpj and clean_cnpj[11] == "1":
            token_cnpj.append(token)
            response = bot.search(clean_cnpj)
            result.append(
                [
                    name,
                    cnpj,
                    response["cadastro"],
                    response["simples"],
                    response["cnd"],
                    response["fgts"],
                    response["cndt"],
                ]
            )

    with open(
        path / "Resultado_consulta.csv", mode="w", newline="", encoding="utf-8-sig"
    ) as file:
        writer = csv.writer(file, delimiter=";")
        writer.writerow(header)
        writer.writerows(result)


if __name__ == "__main__":
    main()
