# 📄 Consulta e Download Automático de Certidões por CNPJ 

Aplicação desenvolvida em Python com interface gráfica em Tkinter para consulta e download automatizado de certidões empresariais a partir de um CNPJ.

O projeto utiliza Camoufox para realizar web scraping com técnicas de navegação que proporcionam maior compatibilidade e estabilidade durante a execução das rotinas de coleta de dados, automatizando a obtenção de documentos e verificações cadastrais em diferentes órgãos e serviços públicos.

## 🚀 Sobre o Projeto

Este projeto surgiu como uma iniciativa de estudo e aprimoramento de conhecimentos em Python, automação web e web scraping.

## ⚠ Aviso Importante ⚠

Os resultados obtidos são gerados por consultas automatizadas em fontes públicas e podem estar sujeitos a indisponibilidades temporárias, alterações nos portais consultados ou falhas de processamento.

Embora o sistema automatize as verificações e o download das certidões, recomenda-se sempre confirmar manualmente qualquer resultado negativo, irregular ou inconsistente antes de tomar decisões administrativas, financeiras ou jurídicas.

Este projeto tem finalidade de automação e auxílio operacional, não substituindo a validação oficial realizada diretamente nos órgãos emissores.

## ✨ Funcionalidades 

* Consulta da situação cadastral da empresa através do CNPJ informado.
* Validação prévia da situação cadastral antes da execução das demais consultas.
* Verificação do enquadramento no Simples Nacional.
* Consulta da Certidão Negativa de Débitos (CND).
* Consulta da Regularidade do Empregador perante o FGTS.
* Consulta da Certidão Negativa de Débitos Trabalhistas (CNDT).
* Exibição dos resultados diretamente na interface gráfica.
* Download automático das certidões e comprovantes disponíveis.

## 🔄 Como funciona 

1. Informe o CNPJ na interface.
2. O sistema consulta a situação cadastral da empresa.
3. Caso a empresa esteja ativa, as demais verificações são iniciadas automaticamente.
4. Os resultados são exibidos na tela.
5. Os documentos encontrados são baixados para armazenamento local.

## 🛠️ Tecnologias utilizadas 

* Python
* Tkinter
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

Este projeto possui uma versão alternativa voltada para processamento em lote de múltiplos CNPJs utilizando planilhas Excel e exportação de resultados em CSV.

Consulte a branch `lote` para mais informações.
