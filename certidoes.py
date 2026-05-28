import io
import re
import random
import base64
import cv2
import numpy as np
import ddddocr

from PIL import Image
from pathlib import Path
from camoufox.sync_api import Camoufox
from time import sleep
from datetime import datetime
from pypdf import PdfReader

class Bot:
    def __init__(self, cnpj, keys):

        self.cnpj = cnpj
        self.keys = keys
        for key in self.keys:
            self.result = {key: None}

        self.date = datetime.now().strftime("%Y/%m/%d")
        self.path = Path.home() / "Downloads" / "Certidoes" / self.date
        self.page = None

        self.proceed = True

    def validateCNPJ(self, cnpj):
        if len(cnpj) != 14 or len(set(cnpj)) == 1:
            return False

        def calculateDigit(slice_data, weights):
            total = sum(int(num) * weight for num, weight in zip(slice_data, weights))
            remainder = total % 11
            return '0' if remainder < 2 else str(11 - remainder)

        weights1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        weights2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]

        digit1 = calculateDigit(cnpj[:12], weights1)
        digit2 = calculateDigit(cnpj[:13], weights2)

        return cnpj[-2:] == (digit1 + digit2)

    def moveMouse(self, box, margin=10):
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

    def download(self, download_btn, name, path=None):
        if path is None:
            path = self.path
        try:
            path.mkdir(parents=True, exist_ok=True)
            with self.page.expect_download(timeout=1500) as download_info:
                self.moveMouse(download_btn, 2)
                download = download_info.value
                download.save_as(f"{path}/{name}.pdf")
        except Exception:
            return

    def printScreen(self, name, path=None, page=None):
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

    def solveCaptcha(self, id, page=None):
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

        _, img_encoded = cv2.imencode('.png', image_final)
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
            self.moveMouse(input_cnpj, 20)
            self.type(input_cnpj)
            checkbox = frame.locator("#checkbox")
            self.moveMouse(checkbox, 20)
            consulte = self.page.locator("button:has-text('Consultar')")
            self.moveMouse(consulte, 10)

            name = self.page.locator("div.section-title:has-text('NOME EMPRESARIAL') + div.section-data").first.inner_text().strip()
            name = re.sub(r'[\\/*?:"<>|]', "", name)
            self.path = self.path / name

            status = self.page.locator("div.section-title:has-text('SITUAÇÃO CADASTRAL') + div.section-data").first.inner_text().strip().capitalize()
            if status.lower() != "ativa":
                motive = self.page.locator("div.section-title:has-text('MOTIVO DE SITUAÇÃO CADASTRAL') + div.section-data").first.inner_text().strip().capitalize()
                self.result["cadastro"] = (f"{status} - {motive}" if motive else status, "#FC1B1B")
                self.proceed = False
                print = self.page.locator("button:has-text('Imprimir')")
                with self.page.context.expect_page() as popup_info:
                    self.moveMouse(print, 10)
                    popup = popup_info.value
                    popup.wait_for_load_state()
                    self.printScreen("Cadastro", page=popup)
            else:
                self.result["cadastro"] = (status, "#00ff37")

        except Exception:
            self.result["cadastro"] = ("Erro no software", "#FC1B1B")

    def simples(self):
        try:
            self.page.goto("https://www8.receita.fazenda.gov.br/SimplesNacional/aplicacoes.aspx?id=21") 
            self.page.wait_for_selector("iframe")
            frame = self.page.frame_locator("iframe")
            input_cnpj = frame.locator("#Cnpj")
            consulte = frame.locator("button:has-text('Consultar')")

            self.moveMouse(input_cnpj, 20)

            self.type(input_cnpj)
            self.moveMouse(consulte, 10)

            self.page.wait_for_selector("iframe")
            frame = self.page.frame_locator("iframe")
            box_status = frame.locator("text=Situação no Simples Nacional").locator("xpath=..")

            box_status.wait_for(state="visible")
            status = box_status.inner_text()
            if "NÃO optante pelo Simples Nacional" in status:
                self.result["simples"] = ("Não optante", "#FC1B1B")
            else:
                self.result["simples"] = ("Optante", "#00ff37")

            pdf_btn = frame.locator("button:has-text('Gerar PDF')")
            self.download(pdf_btn, "Simples")

        except Exception:
            self.result["simples"] = ("Erro no software", "#FC1B1B")

    def cnd(self):
        try:
            self.page.goto("https://servicos.receitafederal.gov.br/servico/certidoes/#/home/cnpj")  
            self.page.wait_for_selector("button:has-text('Aceitar')")
            accept = self.page.locator("button:has-text('Aceitar')")
            input_cnpj = self.page.locator("input[name='niContribuinte']")    
            consulte = self.page.locator("button:has-text('Consultar')")

            self.moveMouse(accept, 5)
            self.moveMouse(input_cnpj, 25)
            self.type(input_cnpj)
            self.moveMouse(consulte, 10)

            self.page.wait_for_selector("button:has-text('Consultar')")
            consulte = self.page.locator("button:has-text('Consultar')")
            self.moveMouse(consulte, 10)

            if self.page.locator(".br-message .description").count():
                error = self.page.locator(".br-message .description").inner_text()
                self.result["cnd"] = (error, "#FC1B1B")
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
                        self.result["cnd"] = (status, "#00ff37")
                    else:
                        self.result["cnd"] = (status, "#FC1B1B")

                    second_copy = row.locator("button:has(i.fa-download)")
                    self.download(second_copy, "CND")
                    break
            if not valid_found:
                self.result["cnd"] = ("Nenhuma certidão válida encontrada", "#FC1B1B")

        except Exception:
            self.result["cnd"] = ("Erro no software", "#FC1B1B")

    def fgts(self):
        try:
            self.page.goto("https://consulta-crf.caixa.gov.br/consultacrf/pages/consultaEmpregador.jsf", wait_until="domcontentloaded") 
            input_cnpj = self.page.locator("input[name='mainForm:txtInscricao1']")

            self.moveMouse(input_cnpj, 30)
            self.type(input_cnpj)

            uf = self.page.locator('#mainForm\\:uf')
            self.moveMouse(uf)
            uf.select_option('SP')
            consulte = self.page.locator("input[value='Consultar']")
            self.moveMouse(consulte, 10)
            
            self.page.wait_for_load_state("domcontentloaded")
            if self.page.locator(".feedback-text").filter(has_not_text="não encontrado").count():
                self.page.wait_for_selector(".feedback-text")
                status = self.page.locator(".feedback-text").inner_text()
                if "está regular" in status.lower():
                    self.result["fgts"] = ("Regular", "#00ff37")
                else:
                    self.result["fgts"] = ("Irregular", "#FC1B1B")
                link = self.page.locator("a[name='mainForm:j_id51']")
                self.moveMouse(link, 3)
                self.page.wait_for_selector("input:has-text('Visualizar')")
                view = self.page.locator("input:has-text('Visualizar')")
                self.moveMouse(view)
                self.page.wait_for_load_state("domcontentloaded")
                self.printScreen("FGTS")
            else:
                self.result["fgts"] = ("Não encontrado", "#FC1B1B")

        except Exception:
            self.result["fgts"] = ("Erro no software", "#FC1B1B")

    def cndt(self, attempt = 0):
        try:
            if attempt == 6:
                self.result["cndt"] = ("Não passou o captcha", "#FC1B1B")
                return

            self.page.goto("https://cndt-certidao.tst.jus.br/inicio.faces")
            self.page.wait_for_selector("input[value='Emitir Certidão']")
            issue1 = self.page.locator("input[value='Emitir Certidão']")
            self.moveMouse(issue1, 5)

            input_cnpj = self.page.locator("#gerarCertidaoForm\\:cpfCnpj")
            self.moveMouse(input_cnpj, 15)
            self.type(input_cnpj)

            captcha_result = self.solveCaptcha("#idImgBase64", attempt)
            input_captcha = self.page.locator("#idCampoResposta")
            self.moveMouse(input_captcha, 15)
            self.type(input_captcha, captcha_result)
            
            self.page.wait_for_selector("input[value='Emitir Certidão']")
            issue2 = self.page.locator("input[value='Emitir Certidão']")

            self.download(issue2, "CNDT")
            if(self.page.locator("#mensagens").count()):
                if("código de validação" in self.page.locator("#mensagens").inner_text().lower()):
                    self.cndt(attempt + 1)
            
            path_test = self.path / "CNDT.pdf"
            if path_test.exists():
                reader = PdfReader(self.path / "CNDT.pdf")
                pdf = reader.pages[0]
                title = pdf.extract_text().splitlines()[0].strip().capitalize()
                if "negativa" in title.lower():
                    self.result["cndt"] = (title, "#00ff37")
                else:
                    self.result["cndt"] = (title, "#FC1B1B")
    
        except Exception:
            self.result["cndt"] = ("Erro no software", "#FC1B1B")

    def search(self):
        if not self.validateCNPJ(self.cnpj):
            for key in self.keys:
                self.result[key] = ("CNPJ inválido!", "#FC1B1B")
            return self.result

        with Camoufox(
            headless=True,
            humanize=False,
            config={
            "navigator.platform":"Win32",
            "navigator.userAgent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:150.0) Gecko/20100101 Firefox/150.0", 
            "navigator.language":"pt-BR",
            "window.outerHeight":728,
            "window.outerWidth":1366
            },
            i_know_what_im_doing=True
            ) as browser:
            self.page = browser.new_page(viewport={"width": 1366, "height": 768})

            self.cadastro()
            if(self.proceed):
                self.simples()
                self.cnd()
                self.fgts()
                self.cndt()
            else:
                for key in self.keys:
                    self.result[key] = ("Situação cadastral diferente de ativa", "#FFFFFF")

        return self.result
