# 📄 Consulta e Download de Certidões em Lote por CNPJ

Aplicação desenvolvida em Python para consulta e download automatizado de certidões empresariais em larga escala a partir de uma planilha contendo múltiplos CNPJs.

O projeto utiliza Camoufox para automatizar a navegação web necessária para obtenção de documentos e verificações cadastrais em diferentes órgãos e serviços públicos. Os dados são processados em lote utilizando Pandas, permitindo a geração de relatórios consolidados em formato CSV.

## 🚀 Sobre o Projeto

Este projeto surgiu como uma evolução da versão com interface gráfica, com o objetivo de aprimorar conhecimentos em Python, automação web, web scraping e processamento de dados utilizando Pandas.

A proposta é automatizar consultas para múltiplas empresas de forma sequencial, reduzindo o trabalho manual em cenários que exigem análise de grandes quantidades de CNPJs.

## ⚠ Aviso Importante ⚠

Os resultados obtidos são gerados por consultas automatizadas em fontes públicas e podem estar sujeitos a indisponibilidades temporárias, alterações nos portais consultados ou falhas de processamento.

Embora o sistema automatize as verificações e o download das certidões, recomenda-se sempre confirmar manualmente qualquer resultado negativo, irregular ou inconsistente antes de tomar decisões administrativas, financeiras ou jurídicas.

Este projeto tem finalidade de automação e auxílio operacional, não substituindo a validação oficial realizada diretamente nos órgãos emissores.

## ✨ Funcionalidades

* Leitura automática de planilhas Excel contendo CNPJs.
* Consulta da situação cadastral das empresas.
* Validação prévia da situação cadastral antes da execução das demais consultas.
* Verificação do enquadramento no Simples Nacional.
* Consulta da Certidão Negativa de Débitos (CND).
* Consulta da Regularidade do Empregador perante o FGTS.
* Consulta da Certidão Negativa de Débitos Trabalhistas (CNDT).
* Download automático das certidões e comprovantes disponíveis.
* Processamento sequencial de múltiplos CNPJs.
* Exportação consolidada dos resultados para arquivo CSV.

## 🔄 Como funciona

1. O sistema lê uma planilha Excel contendo os CNPJs a serem consultados.
2. Cada empresa é processada individualmente.
3. A situação cadastral é validada antes das demais consultas.
4. As verificações e downloads são executados automaticamente.
5. Os resultados são armazenados em memória durante o processamento.
6. Ao final, um arquivo CSV consolidado é gerado com todas as informações obtidas.

## 🛠️ Tecnologias Utilizadas

* Python
* Pandas
* Camoufox
* Web Scraping

## 📦 Instalação

```bash
git clone https://github.com/Pablo-Duque/Certidoes.git
cd Certidoes

pip install -r requirements.txt
```

## ▶️ Execução

```bash
python main.py
```

## 🔀 Outras Versões

Existe também uma versão com interface gráfica desenvolvida em Tkinter para consultas individuais de empresas.

Consulte a branch `main` para mais informações.
