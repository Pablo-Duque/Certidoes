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
from playwright.sync_api import expect
from PIL import Image
from pypdf import PdfReader


class Bot:
    def __init__(self):
        self._cnpj = None
        self._keys = None
        self._path = None
        self._uf = None
        self._close = False

        self._date = datetime.now().strftime("%Y/%m/%d")

        self._camoufox = Camoufox(
            headless=True,
            humanize=False,
            config={
                "navigator.platform": "Win32",
                "navigator.userAgent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; "
                    "x64; rv:150.0) Gecko/20100101 Firefox/150.0"
                ),
                "navigator.language": "pt-BR",
                "window.outerHeight": 728,
                "window.outerWidth": 1366,
            },
            i_know_what_im_doing=True,
        )
        self._browser = self._camoufox.__enter__()
        self._page = self._browser.new_page(
            viewport={
                "width": 1366,
                "height": 768,
            }
        )

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
            self._page.mouse.move(rand_x, rand_y)
            sleep(random.uniform(0.2, 0.5))
            box.click()
            sleep(random.uniform(0.4, 0.7))

    def type(self, box, text=None):
        if text is None:
            text = self._cnpj

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
            path = self._path
        try:
            path.mkdir(parents=True, exist_ok=True)
            with self._page.expect_download(timeout=1500) as download_info:
                self.move_mouse(download_btn, 2)
                download = download_info.value
                download.save_as(f"{path}/{name}.pdf")
        except Exception:
            return

    def print_screen(self, name, path=None, page=None):
        if path is None:
            path = self._path

        if page is None:
            page = self._page

        path.mkdir(parents=True, exist_ok=True)
        image_bytes = page.screenshot(full_page=True)
        image = Image.open(io.BytesIO(image_bytes))
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")
        image.save(str(path / f"{name}.pdf"), "PDF", resolution=100)

    def solve_captcha(self, id):
        self._page.wait_for_selector(f"{id}[src]", timeout=10000)
        code = self._page.get_attribute(id, "src").split(",")[1].strip()
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
            self._page.goto(
                "https://solucoes.receita.fazenda.gov.br/Servicos/cnpjreva/"
            )
            self._page.wait_for_selector("iframe", timeout=5000)
            frame = self._page.frame_locator("iframe").nth(0)
            input_cnpj = self._page.locator("input[type='text']")
            self.move_mouse(input_cnpj, 20)
            self.type(input_cnpj)
            checkbox = frame.locator("#checkbox")
            self.move_mouse(checkbox, 20)
            expect(checkbox).to_have_attribute("aria-checked", "true", timeout=5000)
            consulte = self._page.locator("button:has-text('Consultar')")
            self.move_mouse(consulte, 10)

            name = (
                self._page.locator(
                    "div.section-title:has-text('NOME EMPRESARIAL') + div.section-data"
                )
                .first.inner_text()
                .strip()
            )
            name = re.sub(r'[\\/*?:"<>|]', "", name)
            self._path = self._path / name

            uf = (
                self._page.locator(
                    "div.section-title:has-text('UF') + div.section-data"
                )
                .first.inner_text()
                .strip()
            )
            self._uf = uf
            status = (
                self._page.locator(
                    "div.section-title:has-text('SITUAÇÃO CADASTRAL') + div.section-data"
                )
                .first.inner_text()
                .strip()
                .capitalize()
            )
            if status.lower() != "ativa":
                motive = (
                    self._page.locator(
                        "div.section-title:has-text('MOTIVO DE SITUAÇÃO CADASTRAL') + div.section-data"
                    )
                    .first.inner_text()
                    .strip()
                    .capitalize()
                )
                self._result["cadastro"] = (
                    f"{status} - {motive}" if motive else status,
                    "#FC1B1B",
                )
                self._proceed = False
                print_btn = self._page.locator("button:has-text('Imprimir')")
                with self._page.context.expect_page() as popup_info:
                    self.move_mouse(print_btn, 10)
                    popup = popup_info.value
                    popup.wait_for_load_state()
                    self.print_screen("Cadastro", page=popup)
            else:
                self._result["cadastro"] = (status, "#00ff37")

        except Exception as e:
            print(e)
            self.print_screen("Erro Cadastro")
            if "timeout" in str(e).lower():
                self._result["cadastro"] = ("Página não respondeu", "#FC1B1B")
            else:
                self._result["cadastro"] = ("Erro no software", "#FC1B1B")

    def simples(self):
        try:
            self._page.goto(
                "https://www8.receita.fazenda.gov.br/SimplesNacional/aplicacoes.aspx?id=21"
            )
            self._page.wait_for_selector("iframe", timeout=5000)
            frame = self._page.frame_locator("iframe")
            input_cnpj = frame.locator("#Cnpj")
            consulte = frame.locator("button:has-text('Consultar')")

            self.move_mouse(input_cnpj, 20)

            self.type(input_cnpj)
            self.move_mouse(consulte, 10)

            self._page.wait_for_selector("iframe", timeout=5000)
            frame = self._page.frame_locator("iframe")
            box_status = frame.locator("text=Situação no Simples Nacional").locator(
                "xpath=.."
            )

            box_status.wait_for(state="visible")
            status = box_status.inner_text()
            if "nao optante pelo simples nacional" in self.remove_accent(
                status.lower()
            ):
                self._result["simples"] = ("Não optante", "#FC1B1B")
            else:
                self._result["simples"] = ("Optante", "#00ff37")

            pdf_btn = frame.locator("button:has-text('Gerar PDF')")
            self.download(pdf_btn, "Simples")

        except Exception as e:
            print(e)
            self.print_screen("Erro Simples")
            if "timeout" in str(e).lower():
                self._result["simples"] = ("Página não respondeu", "#FC1B1B")
            else:
                self._result["simples"] = ("Erro no software", "#FC1B1B")

    def cnd(self):
        try:
            self._page.goto(
                "https://servicos.receitafederal.gov.br/servico/certidoes/#/home/cnpj",
                wait_until="domcontentloaded",
                timeout=10000,
            )

            input_cnpj = self._page.locator("input[name='niContribuinte']")
            consulte = self._page.locator("button:has-text('Consultar')")
            self.move_mouse(input_cnpj, 25)
            self.type(input_cnpj)
            if self._page.locator("button:has-text('Aceitar')").count():
                accept = self._page.locator("button:has-text('Aceitar')")
                self.move_mouse(accept, 5)
            self.move_mouse(consulte, 10)

            if not self._page.locator("button:has-text('Consultar')").is_visible():
                self._page.wait_for_selector("button:has-text('Aceitar')", timeout=5000)
                accept = self._page.locator("button:has-text('Aceitar')")
                self.move_mouse(accept, 5)
            
            consulte = self._page.locator("button:has-text('Consultar')")
            self.move_mouse(consulte, 10)

            if self._page.locator(".br-message .description").count():
                error = self._page.locator(".br-message .description").inner_text()
                self._result["cnd"] = (error[:70], "#FC1B1B")
                return

            self._page.wait_for_selector("datatable-body-row", timeout=5000)
            rows = self._page.locator("datatable-body-row")
            valid_found = False

            for i in range(rows.count()):
                row = rows.nth(i)
                status = row.locator("span").nth(2).inner_text().strip()
                situation = row.locator("span").nth(5).inner_text().strip()

                if situation == "Válida":
                    valid_found = True
                    if "negativa" in status.lower():
                        self._result["cnd"] = (status, "#00ff37")
                    else:
                        self._result["cnd"] = (status, "#FC1B1B")

                    second_copy = row.locator("button:has(i.fa-download)")
                    self.download(second_copy, "CND")
                    break
            if not valid_found:
                self._result["cnd"] = (
                    "Nenhuma certidão válida encontrada",
                    "#FC1B1B",
                )

        except Exception as e:
            print(e)
            self.print_screen("Erro CND")
            if "timeout" in str(e).lower():
                self._result["cnd"] = ("Página não respondeu", "#FC1B1B")
            else:
                self._result["cnd"] = ("Erro no software", "#FC1B1B")

    def fgts(self):
        try:
            self._page.goto(
                "https://consulta-crf.caixa.gov.br/consultacrf/pages/consultaEmpregador.jsf",
                wait_until="domcontentloaded",
                timeout=10000,
            )
            input_cnpj = self._page.locator("input[name='mainForm:txtInscricao1']")

            self.move_mouse(input_cnpj, 30)
            self.type(input_cnpj)

            uf = self._page.locator("#mainForm\\:uf")
            self.move_mouse(uf)
            uf.select_option(self._uf)
            consulte = self._page.locator("input[value='Consultar']")
            self.move_mouse(consulte, 10)

            self._page.wait_for_load_state("domcontentloaded", timeout=10000)
            # if self._page.locator(".feedback-text").count():
            self._page.wait_for_selector(".feedback-text", timeout=5000)
            status = self._page.locator(".feedback-text").inner_text()
            if "nao encontrado" in self.remove_accent(status.lower()):
                self._result["fgts"] = ("Não encontrado", "#FC1B1B")
            elif "informacoes disponiveis nao sao suficientes" in self.remove_accent(
                status.lower()
            ):
                self._result["fgts"] = ("Informações insuficientes", "#FC1B1B")
            elif "esta regular" in self.remove_accent(status.lower()):
                self._result["fgts"] = ("Regular", "#00ff37")
                link = self._page.locator("a:has-text('Certificado de Regularidade')")
                self.move_mouse(link, 3)
                self._page.wait_for_selector(
                    "input:has-text('Visualizar')", timeout=5000
                )
                view = self._page.locator("input:has-text('Visualizar')")
                self.move_mouse(view)
                self._page.wait_for_selector("input:has-text('Imprimir')", timeout=5000)
                self.print_screen("FGTS")
            else:
                self.print_screen("FGTS")
                self._result["fgts"] = ("Irregular", "#FC1B1B")

        except Exception as e:
            print(e)
            self.print_screen("Erro FGTS")
            if "timeout" in str(e).lower():
                self._result["fgts"] = ("Página não respondeu", "#FC1B1B")
            else:
                self._result["fgts"] = ("Erro no software", "#FC1B1B")

    def cndt(self, attempt=0):
        try:
            if attempt == 6:
                self._result["cndt"] = ("Não passou o captcha", "#FC1B1B")
                return

            self._page.goto("https://cndt-certidao.tst.jus.br/inicio.faces")
            self._page.wait_for_selector("input[value='Emitir Certidão']", timeout=5000)
            issue1 = self._page.locator("input[value='Emitir Certidão']")
            self.move_mouse(issue1, 5)

            self._page.wait_for_selector("#gerarCertidaoForm\\:cpfCnpj", timeout=5000)
            input_cnpj = self._page.locator("#gerarCertidaoForm\\:cpfCnpj")
            self.move_mouse(input_cnpj, 15)
            self.type(input_cnpj)

            captcha_result = self.solve_captcha("#idImgBase64")
            input_captcha = self._page.locator("#idCampoResposta")
            self.move_mouse(input_captcha, 15)
            self.type(input_captcha, captcha_result)

            self._page.wait_for_selector("input[value='Emitir Certidão']", timeout=5000)
            issue2 = self._page.locator("input[value='Emitir Certidão']")

            self.download(issue2, "CNDT")

            path_test = self._path / "CNDT.pdf"
            if path_test.exists():
                reader = PdfReader(self._path / "CNDT.pdf")
                pdf = reader.pages[0]
                title = pdf.extract_text().splitlines()[0].strip().capitalize()
                if "negativa" in title.lower():
                    self._result["cndt"] = ("Negativa", "#00ff37")
                    if "positiva" in title.lower():
                        self._result["cndt"] = (
                            "Positiva com efeitos de negativa",
                            "#00ff37",
                        )
                else:
                    self._result["cndt"] = ("Positiva", "#FC1B1B")
            else:
                if self._page.locator("#mensagens").count():
                    if (
                        "código de validação"
                        in self._page.locator("#mensagens").inner_text().lower()
                    ):
                        self.cndt(attempt + 1)
                else:
                    self.print_screen("Erro CNDT")
                    self._result["cndt"] = ("Erro no download", "#FC1B1B")

        except Exception as e:
            print(e)
            self.print_screen("Erro CNDT")
            if "timeout" in str(e).lower():
                self._result["cndt"] = ("Página não respondeu", "#FC1B1B")
            else:
                self._result["cndt"] = ("Erro no software", "#FC1B1B")

    def search(self, cnpj, keys):
        self._path = Path.home() / "Downloads" / "Certidoes"  # / self._date
        self._proceed = True
        self._cnpj = cnpj
        self._keys = keys
        self._result = {key: None for key in self._keys}

        self.cadastro()
        if self._proceed and not self._close:
            if "simples" in self._keys and not self._close:
                self.simples()
            if "cnd" in self._keys and not self._close:
                self.cnd()
            if "fgts" in self._keys and not self._close:
                self.fgts()
            if "cndt" in self._keys and not self._close:
                self.cndt()
        else:
            for key in self._keys:
                if key != "cadastro":
                    self._result[key] = (
                        "Situação cadastral diferente de ativa",
                        "#FFFFFF",
                    )

        return self._result

    def close(self):
        self._close = True
        if self._browser:
            self._browser.close()
        self._camoufox.__exit__(None, None, None)
