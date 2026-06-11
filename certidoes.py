import base64
import io
import random
import re
import unicodedata
from datetime import datetime
from pathlib import Path
from time import sleep

import cv2
import ddddocr
import numpy as np
from camoufox.sync_api import Camoufox
from PIL import Image
from pypdf import PdfReader


class Bot:
    def __init__(self,keys):

        self.keys = keys
        self.date = datetime.now().strftime("%Y/%m/%d")
        self.path = Path.home() / "Downloads" / "Certidoes"  # / self.date
        self.cnpj = None
        self.page = None
        self.uf = None
        self.proceed = True

    def validate_cnpj(self, cnpj):
        if len(cnpj) != 14 or len(set(cnpj)) == 1:
            return False

        def calculate_digit(slice_data, weights):
            total = sum(int(num) * weight for num, weight in zip(slice_data, weights))
            remainder = total % 11
            return "0" if remainder < 2 else str(11 - remainder)

        weights1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        weights2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]

        digit1 = calculate_digit(cnpj[:12], weights1)
        digit2 = calculate_digit(cnpj[:13], weights2)

        return cnpj[-2:] == (digit1 + digit2)

    def move_mouse(self, box, margin=10):
        bounding = box.bounding_box()
        if bounding:
            margin = min(margin, bounding["width"] / 3, bounding["height"] / 3)
            min_x = bounding["x"] + margin
            max_x = bounding["x"] + bounding["width"] - margin

            min_y = bounding["y"] + margin
            max_y = bounding["y"] + bounding["height"] - margin

            rand_x = random.uniform(min_x, max_x)
            rand_y = random.uniform(min_y, max_y)
            self.page.mouse.move(rand_x, rand_y)
            sleep(random.uniform(0.2, 0.5))
            box.click()
            sleep(random.uniform(0.4, 0.7))

    def type(self, box, text=None):
        if text is None:
            text = self.cnpj

        for letter in text:
            box.type(letter, delay=random.uniform(100, 265))
        sleep(random.uniform(0.2, 0.7))

    def remove_accent(self, text):
        return "".join(
            c
            for c in unicodedata.normalize("NFD", text)
            if unicodedata.category(c) != "Mn"
        )

    def download(self, download_btn, name, path=None):
        if path is None:
            path = self.path
        try:
            path.mkdir(parents=True, exist_ok=True)
            with self.page.expect_download(timeout=1500) as download_info:
                self.move_mouse(download_btn, 2)
                download = download_info.value
                download.save_as(f"{path}/{name}.pdf")
        except Exception:
            return

    def print_screen(self, name, path=None, page=None):
        if path is None:
            path = self.path

        if page is None:
            page = self.page

        path.mkdir(parents=True, exist_ok=True)
        image_bytes = page.screenshot(full_page=True)
        image = Image.open(io.BytesIO(image_bytes))
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")
        image.save(str(path / f"{name}.pdf"), "PDF", resolution=100)

    def solve_captcha(self, id, page=None):
        if page is None:
            page = self.page

        self.page.wait_for_selector(f"{id}[src]")
        code = self.page.get_attribute(id, "src").split(",")[1].strip()
        bytes = base64.b64decode(code)

        nparr = np.frombuffer(bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blur = cv2.medianBlur(gray, 5)
        _, thresh = cv2.threshold(blur, 220, 255, cv2.THRESH_BINARY)
        kernel = np.ones((2, 2), np.uint8)
        image_final = cv2.morphologyEx(thresh, cv2.MORPH_ERODE, kernel)

        _, img_encoded = cv2.imencode(".png", image_final)
        ocr = ddddocr.DdddOcr(show_ad=False)
        bytes = img_encoded.tobytes()
        result = ocr.classification(bytes)

        return result

    def cadastro(self):
        try:
            self.page.goto("https://solucoes.receita.fazenda.gov.br/Servicos/cnpjreva/")
            self.page.wait_for_selector("iframe")
            frame = self.page.frame_locator("iframe").nth(0)
            input_cnpj = self.page.locator("input[type='text']")
            self.move_mouse(input_cnpj, 20)
            self.type(input_cnpj)
            checkbox = frame.locator("#checkbox")
            self.move_mouse(checkbox, 20)
            consulte = self.page.locator("button:has-text('Consultar')")
            self.move_mouse(consulte, 10)

            name = (
                self.page.locator(
                    "div.section-title:has-text('NOME EMPRESARIAL') + div.section-data"
                )
                .first.inner_text()
                .strip()
            )
            name = re.sub(r'[\\/*?:"<>|]', "", name)
            self.path = self.path / name

            uf = (
                self.page.locator("div.section-title:has-text('UF') + div.section-data")
                .first.inner_text()
                .strip()
            )
            self.uf = uf
            status = (
                self.page.locator(
                    "div.section-title:has-text('SITUAÇÃO CADASTRAL') + div.section-data"
                )
                .first.inner_text()
                .strip()
                .capitalize()
            )
            if status.lower() != "ativa":
                motive = (
                    self.page.locator(
                        "div.section-title:has-text('MOTIVO DE SITUAÇÃO CADASTRAL') + div.section-data"
                    )
                    .first.inner_text()
                    .strip()
                    .capitalize()
                )
                self.result["cadastro"] = (
                    f"{status} - {motive}" if motive else status
                )
                self.proceed = False
                print = self.page.locator("button:has-text('Imprimir')")
                with self.page.context.expect_page() as popup_info:
                    self.move_mouse(print, 10)
                    popup = popup_info.value
                    popup.wait_for_load_state()
                    self.print_screen("Cadastro", page=popup)
            else:
                self.result["cadastro"] = (status)

        except Exception as e:
            print(e)
            self.print_screen("Erro Cadastro")
            if "timeout" in str(e).lower():
                self.result["cadastro"] = ("Página não respondeu")
            else:
                self.result["cadastro"] = ("Erro no software")

    def simples(self):
        try:
            self.page.goto(
                "https://www8.receita.fazenda.gov.br/SimplesNacional/aplicacoes.aspx?id=21"
            )
            self.page.wait_for_selector("iframe")
            frame = self.page.frame_locator("iframe")
            input_cnpj = frame.locator("#Cnpj")
            consulte = frame.locator("button:has-text('Consultar')")

            self.move_mouse(input_cnpj, 20)

            self.type(input_cnpj)
            self.move_mouse(consulte, 10)

            self.page.wait_for_selector("iframe")
            frame = self.page.frame_locator("iframe")
            box_status = frame.locator("text=Situação no Simples Nacional").locator(
                "xpath=.."
            )

            box_status.wait_for(state="visible")
            status = box_status.inner_text()
            if "nao optante pelo simples nacional" in self.remove_accent(
                status.lower()
            ):
                self.result["simples"] = ("Não optante")
            else:
                self.result["simples"] = ("Optante")

            pdf_btn = frame.locator("button:has-text('Gerar PDF')")
            self.download(pdf_btn, "Simples")

        except Exception as e:
            print(e)
            self.print_screen("Erro Simples")
            if "timeout" in str(e).lower():
                self.result["simples"] = ("Página não respondeu")
            else:
                self.result["simples"] = ("Erro no software")

    def cnd(self):
        try:
            self.page.goto(
                "https://servicos.receitafederal.gov.br/servico/certidoes/#/home/cnpj"
            )
            self.page.wait_for_selector("button:has-text('Aceitar')")
            accept = self.page.locator("button:has-text('Aceitar')")
            input_cnpj = self.page.locator("input[name='niContribuinte']")
            consulte = self.page.locator("button:has-text('Consultar')")

            self.move_mouse(accept, 5)
            self.move_mouse(input_cnpj, 25)
            self.type(input_cnpj)
            self.move_mouse(consulte, 10)

            self.page.wait_for_selector("button:has-text('Consultar')")
            consulte = self.page.locator("button:has-text('Consultar')")
            self.move_mouse(consulte, 10)

            if self.page.locator(".br-message .description").count():
                error = self.page.locator(".br-message .description").inner_text()
                self.result["cnd"] = (error)
                return

            self.page.wait_for_selector("datatable-body-row")
            rows = self.page.locator("datatable-body-row")
            valid_found = False

            for i in range(rows.count()):
                row = rows.nth(i)
                status = row.locator("span").nth(2).inner_text().strip()
                situation = row.locator("span").nth(5).inner_text().strip()

                if situation == "Válida":
                    valid_found = True
                    if "negativa" in status.lower():
                        self.result["cnd"] = (status)
                    else:
                        self.result["cnd"] = (status)

                    second_copy = row.locator("button:has(i.fa-download)")
                    self.download(second_copy, "CND")
                    break
            if not valid_found:
                self.result["cnd"] = (
                    "Nenhuma certidão válida encontrada"
                )

        except Exception as e:
            print(e)
            self.print_screen("Erro CND")
            if "timeout" in str(e).lower():
                self.result["cnd"] = ("Página não respondeu")
            else:
                self.result["cnd"] = ("Erro no software")

    def fgts(self):
        try:
            self.page.goto(
                "https://consulta-crf.caixa.gov.br/consultacrf/pages/consultaEmpregador.jsf",
                wait_until="domcontentloaded",
            )
            input_cnpj = self.page.locator("input[name='mainForm:txtInscricao1']")

            self.move_mouse(input_cnpj, 30)
            self.type(input_cnpj)

            uf = self.page.locator("#mainForm\\:uf")
            self.move_mouse(uf)
            uf.select_option(self.uf)
            consulte = self.page.locator("input[value='Consultar']")
            self.move_mouse(consulte, 10)

            self.page.wait_for_load_state("domcontentloaded")
            # if self.page.locator(".feedback-text").count():
            self.page.wait_for_selector(".feedback-text")
            status = self.page.locator(".feedback-text").inner_text()
            if "nao encontrado" in self.remove_accent(status.lower()):
                self.result["fgts"] = ("Não encontrado")
            elif "informacoes disponiveis nao sao suficientes" in self.remove_accent(
                status.lower()
            ):
                self.result["fgts"] = ("Informações insuficientes")
            elif "esta regular" in self.remove_accent(status.lower()):
                self.result["fgts"] = ("Regular")
                link = self.page.locator("a:has-text('Certificado de Regularidade')")
                self.move_mouse(link, 3)
                self.page.wait_for_selector("input:has-text('Visualizar')")
                view = self.page.locator("input:has-text('Visualizar')")
                self.move_mouse(view)
                self.page.wait_for_selector("input:has-text('Imprimir')")
                self.print_screen("FGTS")
            else:
                self.print_screen("FGTS")
                self.result["fgts"] = ("Irregular")

        except Exception as e:
            print(e)
            self.print_screen("Erro FGTS")
            if "timeout" in str(e).lower():
                self.result["fgts"] = ("Página não respondeu")
            else:
                self.result["fgts"] = ("Erro no software")

    def cndt(self, attempt=0):
        try:
            if attempt == 6:
                self.result["cndt"] = ("Não passou o captcha")
                return

            self.page.goto("https://cndt-certidao.tst.jus.br/inicio.faces")
            self.page.wait_for_selector("input[value='Emitir Certidão']")
            issue1 = self.page.locator("input[value='Emitir Certidão']")
            self.move_mouse(issue1, 5)

            self.page.wait_for_selector("#gerarCertidaoForm\\:cpfCnpj")
            input_cnpj = self.page.locator("#gerarCertidaoForm\\:cpfCnpj")
            self.move_mouse(input_cnpj, 15)
            self.type(input_cnpj)

            captcha_result = self.solve_captcha("#idImgBase64", attempt)
            input_captcha = self.page.locator("#idCampoResposta")
            self.move_mouse(input_captcha, 15)
            self.type(input_captcha, captcha_result)

            self.page.wait_for_selector("input[value='Emitir Certidão']")
            issue2 = self.page.locator("input[value='Emitir Certidão']")

            self.download(issue2, "CNDT")

            path_test = self.path / "CNDT.pdf"
            if path_test.exists():
                reader = PdfReader(self.path / "CNDT.pdf")
                pdf = reader.pages[0]
                title = pdf.extract_text().splitlines()[0].strip().capitalize()
                if "negativa" in title.lower():
                    self.result["cndt"] = ("Negativa")
                    if "positiva" in title.lower():
                        self.result["cndt"] = (
                            "Positiva com efeitos de negativa"
                        )
                else:
                    self.result["cndt"] = ("Positiva")
            else:
                if self.page.locator("#mensagens").count():
                    if (
                        "código de validação"
                        in self.page.locator("#mensagens").inner_text().lower()
                    ):
                        self.cndt(attempt + 1)
                else:
                    self.print_screen("Erro CNDT")
                    self.result["cndt"] = ("Erro no download")

        except Exception as e:
            print(e)
            self.print_screen("Erro CNDT")
            if "timeout" in str(e).lower():
                self.result["cndt"] = ("Página não respondeu")
            else:
                self.result["cndt"] = ("Erro no software")

    def search(self, cnpj):
        self.result = {key: None for key in self.keys}
        if not self.validate_cnpj(cnpj):
            for key in self.keys:
                self.result[key] = ("CNPJ inválido!")
            return self.result

        self.cnpj = cnpj

        with Camoufox(
            headless=True,
            humanize=False,
            config={
                "navigator.platform": "Win32",
                "navigator.userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; "
                "x64; rv:150.0) Gecko/20100101 Firefox/150.0",
                "navigator.language": "pt-BR",
                "window.outerHeight": 728,
                "window.outerWidth": 1366,
            },
            i_know_what_im_doing=True,
        ) as browser:
            self.page = browser.new_page(viewport={"width": 1366, "height": 768})

            self.cadastro()
            if self.proceed:
                self.simples()
                self.cnd()
                self.fgts()
                self.cndt()
            else:
                for key in self.keys:
                    self.result[key] = (
                        "Situação cadastral diferente de ativa"
                    )

        return self.result
