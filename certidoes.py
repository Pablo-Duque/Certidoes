import random
import re
import io
from PIL import Image
from pathlib import Path
from camoufox.sync_api import Camoufox
from time import sleep
from datetime import datetime

class Bot:
    def __init__(self, cnpj):
        self.cnpj = cnpj
        self.date = datetime.now().strftime("%Y/%m/%d")
        self.path = Path.home() / "Downloads" / "Certidoes" / self.date
        self.page = None
        self.result = {
            "simples": None,
            "cnd": None,
            "fgts": None
        }

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

    def type(self, box):
        for letter in self.cnpj:
            box.type(letter, delay=random.uniform(100, 280))
        sleep(random.uniform(0.2, 0.7))

    def simples(self):
        try:
            self.page.goto("https://www8.receita.fazenda.gov.br/SimplesNacional/aplicacoes.aspx?id=21") 

            self.page.wait_for_selector("iframe")
            frame = self.page.frame_locator("iframe")
            inputCNPJ = frame.locator("#Cnpj")
            consulte = frame.locator("button:has-text('Consultar')")

            self.moveMouse(inputCNPJ, 10)

            self.type(inputCNPJ)

            self.moveMouse(consulte, 5)

            self.page.wait_for_selector("iframe")
            frame = self.page.frame_locator("iframe")
            box_status = frame.locator("text=Situação no Simples Nacional").locator("xpath=..")

            box_status.wait_for(state="visible")

            status = box_status.inner_text()
            if "NÃO optante pelo Simples Nacional" in status:
                self.result["simples"] = ("Não optante", "#FC1B1B")
            else:
                self.result["simples"] = ("Optante", "#00ff37")

            btnPDF = frame.locator("button:has-text('Gerar PDF')")

            name = frame.locator(".panel-body .spanValorVerde").nth(1).inner_text()
            name = re.sub(r'[\\/*?:"<>|]', "", name).strip()
            self.path = self.path / name
            with self.page.expect_download() as download_info:
                self.moveMouse(btnPDF, 5)
                download = download_info.value
                download.save_as(f"{self.path}/Simples.pdf")

        except Exception:
            self.result["simples"] = ("Erro no software", "#FC1B1B")

    def cnd(self):
        try:
            self.page.goto("https://servicos.receitafederal.gov.br/servico/certidoes/#/home/cnpj")  
            self.page.wait_for_selector("button:has-text('Aceitar')")
            accept = self.page.locator("button:has-text('Aceitar')")
            inputCNPJ = self.page.locator("input[name='niContribuinte']")    
            consulte = self.page.locator("button:has-text('Consultar')")

            self.moveMouse(accept, 5)
            self.moveMouse(inputCNPJ, 10)
            self.type(inputCNPJ)
            self.moveMouse(consulte, 10)

            self.page.wait_for_selector("button:has-text('Consultar')")
            consulte = self.page.locator("button:has-text('Consultar')")
            self.moveMouse(consulte, 10)

            if self.page.locator(".br-message .description").count():
                error = self.page.locator(".br-message .description").inner_text()
                self.result["cnd"] = (error, "#FC1B1B")

            rows = self.page.locator("datatable-body-row")
            valid_found = False

            for i in range(rows.count()):
                row = rows.nth(i)
                status = row.locator("span").nth(2).inner_text().strip()
                situation = row.locator("span").nth(5).inner_text().strip()
                
                if situation == "Válida":
                    valid_found = True
                    if "positiva".lower() in status.lower():
                        self.result["cnd"] = (status, "#00ff37")
                    else:
                        self.result["cnd"] = (status, "#FC1B1B")

                    secondCopy = row.locator("button:has(i.fa-download)")
                    with self.page.expect_download() as download_info:
                                self.moveMouse(secondCopy, 2)
                                download = download_info.value
                                download.save_as(f"{self.path}/CND.pdf")
                    break
            if not valid_found:
                self.result["cnd"] = ("Nenhuma certidão válida encontrada", "#FC1B1B")

        except Exception:
            self.result["cnd"] = ("Erro no software", "#FC1B1B")

    def fgts(self):
        try:
            self.page.goto("https://consulta-crf.caixa.gov.br/consultacrf/pages/consultaEmpregador.jsf", wait_until="domcontentloaded") 
            self.page.wait_for_selector("input[name='mainForm:txtInscricao1']")
            inputCNPJ = self.page.locator("input[name='mainForm:txtInscricao1']")

            self.moveMouse(inputCNPJ, 10)
            self.type(inputCNPJ)

            uf = self.page.locator('#mainForm\\:uf')
            self.moveMouse(uf)
            uf.select_option('SP')
            consulte = self.page.locator("input[value='Consultar']")
            self.moveMouse(consulte, 10)
            
            self.page.wait_for_load_state("domcontentloaded")
            if self.page.locator(".feedback-text").count():
                self.page.wait_for_selector(".feedback-text")
                status = self.page.locator(".feedback-text").inner_text()
                if "está regular".lower() in status.lower():
                    self.result["fgts"] = ("Regular", "#00ff37")
                else:
                    self.result["fgts"] = ("Irregular", "#FC1B1B")
                link = self.page.locator("a[name='mainForm:j_id51']")
                self.moveMouse(link, 3)
                self.page.wait_for_selector("input:has-text('Visualizar')")
                view = self.page.locator("input:has-text('Visualizar')")
                self.moveMouse(view)
                sleep(1.5)
                image_bytes = self.page.screenshot(full_page=True)
                image = Image.open(io.BytesIO(image_bytes))

                if image.mode in ("RGBA", "P"):
                    image = image.convert("RGB")
                image.save(str(self.path / "FGTS.pdf"), "PDF", resolution=100.0)
            else:
                self.result["fgts"] = ("Não encontrado", "#FC1B1B")

        except Exception:
            self.result["fgts"] = ("Erro no software", "#FC1B1B")

    def search(self):
        if not self.validateCNPJ(self.cnpj):
            self.result["simples"] = ("CNPJ inválido!", "#FC1B1B")
            self.result["cnd"] = ("CNPJ inválido!", "#FC1B1B")
            self.result["fgts"] = ("CNPJ inválido!", "#FC1B1B")
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
            self.simples()
            self.cnd()
            self.fgts()
        return self.result