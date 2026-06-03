import csv
from pathlib import Path

import pandas as pd

from certidoes import Bot


def main():
    path = Path.home() / "Downloads" / "Teste.xlsx"
    df = pd.read_excel(path, usecols=[4,5,16])
    df.columns = ["name","cnpj","type"]
    df = df[df["type"] == "Pessoa Jurídica"]
    map = df.set_index('cnpj')['name'].to_dict()

    keys = ["cadastro", "simples", "cnd", "fgts", "cndt"]
    labels = {
        "cadastro": "Situação Cadastral",
        "simples": "Simples",
        "cnd": "CND",
        "fgts": "FGTS",
        "cndt": "CNDT",
    }
    header = []
    for key in keys:
        header.append(labels[key])

    bot = Bot(keys)

    for cnpj, name in map.items():
        response = bot.search(cnpj)
        result.append()

# result precisa ser nesse formato:
# dados = [
#     ['Notebook', 'Eletrônicos', '4500.00', '10'],
#     ['Celular', 'Eletrônicos', '2500.00', '25'],
#     ['Teclado', 'Acessórios', '150.00', '50'],
#     ['Mouse', 'Acessórios', '80.00', '100'],
#     ['Monitor', 'Eletrônicos', '1200.00', '15']
# ]

    with open("Resultado_consulta.csv", mode='w', newline='', encoding='utf-8-sig') as file:
        writer = csv.writer(file, delimiter=';')
        writer.writerow(header)
        writer.writerows(result.items())


if __name__ == "__main__":
    main()