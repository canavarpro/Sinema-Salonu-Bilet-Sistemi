import sys
import os
import requests
import re  # Bulduğunuz kodun regex mantığı için gerekli
from bs4 import BeautifulSoup
from PyQt6 import QtWidgets, QtGui, QtCore
from pymongo import MongoClient
from functools import partial 

# Arayüz dosyasını içe aktar
try:
    from sinemagercek_ui import Ui_Dialog
except ImportError:
    app = QtWidgets.QApplication(sys.argv)
    QtWidgets.QMessageBox.critical(None, "py dosyası yok")
    sys.exit()

# --- SENİN BULDUĞUN KODUN ENTEGRE EDİLMİŞ HALİ ---
def film_resmi_indir(film_adi):
    """
    Kullanıcının StackOverflow'dan bulduğu 'gstatic.com' tabanlı,
    Python 3'e uyarlanmış garanti resim indirme fonksiyonu.
    """
    try:
        print(f"Aranıyor (Gstatic Yöntemi): {film_adi}...")
        
        # Senin bulduğun query mantığı
        query = f"{film_adi} film afişi"
        query = query.split()
        query = '+'.join(query)
        
        # Google Görseller URL yapısı
        url = "https://www.google.co.in/search?q=" + query + "&source=lnms&tbm=isch"
        
        # Header (Tarayıcı gibi görünmek için)
        header = {'User-Agent': 'Mozilla/5.0'}
        
        # İstek atma (urllib2 yerine requests kullanıyoruz)
        response = requests.get(url, headers=header)
        soup = BeautifulSoup(response.content, "html.parser")

        # --- ORİJİNAL KODDAKİ MANTIK BURASI ---
        # "gstatic.com" içeren resimleri bul (Thumbnail oldukları için garanti yüklenirler)
        images = [a['src'] for a in soup.find_all("img", {"src": re.compile("gstatic.com")})]
        
        if not images:
            print("Gstatic resmi bulunamadı.")
            return "default.jpg"

        # İlk bulunan resmi al
        resim_url = images[0]
        
        # Dosya adını temizle
        dosya_adi = "".join([c for c in film_adi if c.isalnum() or c in (' ', '-', '_')]).strip().replace(" ", "_") + ".jpg"
        
        # Resmi İndir
        img_data = requests.get(resim_url).content
        with open(dosya_adi, 'wb') as handler:
            handler.write(img_data)
            
        print(f"İşlem başarılı, indirildi: {dosya_adi}")
        return dosya_adi

    except Exception as e:
        print(f"Resim indirme hatası: {e}")
        return "default.jpg"


class DbEditorDialog(QtWidgets.QDialog):
    def __init__(self, filmler_collection):
        super().__init__()
        self.filmler_collection = filmler_collection
        self.setWindowTitle("Film Veritabanı Düzenle")
        self.setFixedSize(400, 350)

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        self.tabs = QtWidgets.QTabWidget()
        layout.addWidget(self.tabs)

        self.tab_ekle = QtWidgets.QWidget()
        self.tabs.addTab(self.tab_ekle, "Film Ekle")
        self.setup_ekle_ui()

        self.tab_kaldir = QtWidgets.QWidget()
        self.tabs.addTab(self.tab_kaldir, "Film Kaldır")
        self.setup_kaldir_ui()

    def setup_ekle_ui(self):
        form_layout = QtWidgets.QFormLayout()
        
        self.input_ad = QtWidgets.QLineEdit()
        self.input_ad.setPlaceholderText("Örn: Avatar 2")
        
        self.input_fiyat = QtWidgets.QSpinBox()
        self.input_fiyat.setRange(0, 1000)
        self.input_fiyat.setValue(150)

        lbl_bilgi = QtWidgets.QLabel("Not: 'Ekle'ye bastığınızda film posteri\notomatik olarak indirilecektir.")
        lbl_bilgi.setStyleSheet("color: #aaa; font-size: 10px;")

        form_layout.addRow("Film Adı:", self.input_ad)
        form_layout.addRow("Bilet Fiyatı (TL):", self.input_fiyat)
        form_layout.addRow("", lbl_bilgi)

        btn_kaydet = QtWidgets.QPushButton("İnternetten Bul ve Ekle")
        btn_kaydet.clicked.connect(self.film_ekle)
        btn_kaydet.setStyleSheet("background-color: #2980b9; color: white; padding: 8px; font-weight: bold;")

        container_layout = QtWidgets.QVBoxLayout()
        container_layout.addLayout(form_layout)
        container_layout.addWidget(btn_kaydet)
        self.tab_ekle.setLayout(container_layout)

    def setup_kaldir_ui(self):
        layout = QtWidgets.QVBoxLayout()
        
        self.liste_filmler = QtWidgets.QListWidget()
        layout.addWidget(self.liste_filmler)
        
        btn_yenile = QtWidgets.QPushButton("Listeyi Yenile")
        btn_yenile.clicked.connect(self.filmleri_listele)
        layout.addWidget(btn_yenile)

        btn_sil = QtWidgets.QPushButton("Seçili Filmi Sil")
        btn_sil.setStyleSheet("background-color: #c0392b; color: white; padding: 5px;")
        btn_sil.clicked.connect(self.film_sil)
        layout.addWidget(btn_sil)

        self.tab_kaldir.setLayout(layout)
        self.filmleri_listele()

    def film_ekle(self):
        ad = self.input_ad.text().strip()
        fiyat = self.input_fiyat.value()

        if not ad:
            QtWidgets.QMessageBox.warning(self, "Hata", "Lütfen bir film adı girin!")
            return

        self.setWindowTitle("Resim Aranıyor... Lütfen Bekleyin...")
        QtWidgets.QApplication.processEvents()

        # Resim indir (Yeni Entegre Edilen Fonksiyon)
        indirilen_resim_yolu = film_resmi_indir(ad)
        
        yeni_film = {
            "ad": ad,
            "fiyat": fiyat,
            "resim": indirilen_resim_yolu 
        }
        
        try:
            self.filmler_collection.insert_one(yeni_film)
            self.setWindowTitle("Film Veritabanı Düzenle")
            
            msg_text = f"'{ad}' başarıyla eklendi!"
            if indirilen_resim_yolu == "default.jpg":
                msg_text += "\n(Resim bulunamadı, varsayılan atandı.)"
            else:
                msg_text += f"\nİndirilen Resim: {indirilen_resim_yolu}"

            QtWidgets.QMessageBox.information(self, "Başarılı", msg_text)
            self.input_ad.clear()
            self.filmleri_listele()
        except Exception as e:
            self.setWindowTitle("Film Veritabanı Düzenle")
            QtWidgets.QMessageBox.critical(self, "Hata", f"Ekleme hatası: {e}")

    def filmleri_listele(self):
        self.liste_filmler.clear()
        filmler = self.filmler_collection.find()
        for film in filmler:
            item = QtWidgets.QListWidgetItem(f"{film['ad']} - {film.get('fiyat', 0)} TL")
            item.setData(QtCore.Qt.ItemDataRole.UserRole, str(film['_id']))
            self.liste_filmler.addItem(item)

    def film_sil(self):
        secili_item = self.liste_filmler.currentItem()
        if not secili_item:
            QtWidgets.QMessageBox.warning(self, "Uyarı", "Lütfen silinecek filmi seçin.")
            return

        film_id = secili_item.data(QtCore.Qt.ItemDataRole.UserRole)
        film_ad = secili_item.text().split(" - ")[0]

        onay = QtWidgets.QMessageBox.question(self, "Onay", f"{film_ad} filmini silmek istediğine emin misin?",
                                              QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)

        if onay == QtWidgets.QMessageBox.StandardButton.Yes:
            from bson.objectid import ObjectId
            try:
                self.filmler_collection.delete_one({"_id": ObjectId(film_id)})
                QtWidgets.QMessageBox.information(self, "Silindi", "Film veritabanından kaldırıldı.")
                self.filmleri_listele()
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Hata", f"Silme hatası: {e}")


# main
class SinemaUygulamasi(QtWidgets.QDialog, Ui_Dialog):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        
        # --- STİL TANIMLARI ---
        self.STYLE_BOS = "QLabel { background-color: #6d6d6d; border: 1px solid #555; color: white; border-radius: 4px; font-weight: bold; }"
        self.STYLE_SECILI = "QLabel { background-color: #27ae60; border: 2px solid #2ecc71; color: white; border-radius: 4px; font-weight: bold; }"
        self.STYLE_DOLU = "QLabel { background-color: #500000; border: 1px solid red; color: #a0a0a0; border-radius: 4px; text-decoration: line-through; }"
        
        self.STYLE_FRAME_BOS = "QFrame { background-color: #6d6d6d; border: 1px solid #555; border-radius: 10px; }"
        self.STYLE_FRAME_SECILI = "QFrame { background-color: #27ae60; border: 2px solid white; border-radius: 10px; }"

        # kutular
        self.kutular = {
            "tam_bilet": self.spinBox_2,
            "ogrenci_bilet": self.spinBox_4,
            "cips": self.spinBox,
            "misir": self.spinBox_6,
            "gozluk": self.spinBox_3,
            "icecek": self.spinBox_5
        }
        #fiyatlardir
        self.ekstra_fiyatlar = {
            "cips": 40, "misir": 50, "gozluk": 20, "icecek": 30
        }

        # db
        try:
            self.client = MongoClient("mongodb+srv://sinema:sinemagercek@cluster0.dawscod.mongodb.net/") 
            self.db = self.client["SinemaDB"]
            self.filmler_table = self.db["Filmler"]
            self.satis_table = self.db["BiletSatis"]
        except Exception as e:
            print(f"Veritabanı Hatası: {e}")
            QtWidgets.QMessageBox.critical(self, "Hata", f"Veritabanı bağlantısı kurulamadı:\n{e}")

        # degiskendir
        self.secilen_film = {"ad": "", "fiyat": 0, "resim": ""}
        self.secilen_seans = None 
        self.secilen_koltuklar = []    
        self.secilen_koltuk_ids = []
        self.islem_turu = "satis" 

        self.filmleri_getir_ve_diz()
        self.koltuklari_bagla()
        self.odeme_ekranini_hazirla()
        self.seanslari_hazirla() 
        try:
            self.buttonBox.accepted.disconnect()
            self.buttonBox.rejected.disconnect()
        except:
            pass
        self.buttonBox.accepted.connect(self.ileri_adim_kontrol)
        self.buttonBox.rejected.connect(self.geri_veya_iptal)

        try:
            self.satinal.clicked.connect(self.alisverisi_baslat)
            self.iadeet.clicked.connect(self.iade_islemini_baslat)
        except AttributeError:
            print("Uyarı: Butonlar bulunamadı.")

        self.giris_ekranina_don()
        
        try:
            self.dbduzenle.clicked.connect(self.db_duzenle_penceresini_ac)
        except AttributeError:
            pass

    def db_duzenle_penceresini_ac(self):
        self.editor = DbEditorDialog(self.filmler_table)
        self.editor.exec()
        self.filmleri_getir_ve_diz()

    def giris_ekranina_don(self):
        self.sifirla()
        self.stackedWidget.setCurrentIndex(4) 
        self.buttonBox.hide() 
        self.setWindowTitle("Sinema Otomasyonu - Hoşgeldiniz")

    def alisverisi_baslat(self):
        self.islem_turu = "satis"
        self.stackedWidget.setCurrentIndex(0) 
        self.buttonBox.show() 
        self.setWindowTitle("Film Seçimi (Satış Modu)")

    def iade_islemini_baslat(self):
        self.islem_turu = "iade"
        self.stackedWidget.setCurrentIndex(0) 
        self.buttonBox.show()
        self.setWindowTitle("İade Modu")
        QtWidgets.QMessageBox.information(self, "İade Modu", "Lütfen iade etmek istediğiniz Filmi seçiniz.")

    def geri_veya_iptal(self):
        idx = self.stackedWidget.currentIndex()
        if idx == 0: 
            self.giris_ekranina_don()
        else:
            cevap = QtWidgets.QMessageBox.question(self, "İptal", "Ana menüye dönmek istiyor musunuz?", 
                                                   QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
            if cevap == QtWidgets.QMessageBox.StandardButton.Yes:
                self.giris_ekranina_don()

    def sifirla(self):
        self.secilen_film = {"ad": "", "fiyat": 0, "resim": ""}
        self.secilen_seans = None
        self.secilen_koltuklar = []
        self.secilen_koltuk_ids = []
        for kutu in self.kutular.values():
            kutu.setValue(0)
        if hasattr(self, 'seans_map'):
             for _, objeler in self.seans_map.items():
                 objeler[1].setStyleSheet(self.STYLE_FRAME_BOS)

    def odeme_ekranini_hazirla(self):
        for kutu in self.kutular.values():
            kutu.valueChanged.connect(self.anlik_fiyat_hesapla)

    def seanslari_hazirla(self):
        self.seans_map = {
            "07:00": [self.seanstikla, self.seanssec],
            "10:00": [self.seanstikla_2, self.seanssec_2],
            "13:00": [self.seanstikla_4, self.seanssec_4],
            "16:00": [self.seanstikla_6, self.seanssec_6],
            "19:00": [self.seanstikla_7, self.seanssec_7],
            "21:00": [self.seanstikla_9, self.seanssec_9],
            "00:00": [self.seanstikla_5, self.seanssec_5],
            "03:00": [self.seanstikla_8, self.seanssec_8]
        }
        for saat, objeler in self.seans_map.items():
            buton = objeler[0]
            buton.clicked.connect(partial(self.seans_secildi, saat))

    def tum_koltuklari_getir(self):
        for attr_name in dir(self):
            if attr_name.startswith("koltuktikla_"):
                buton = getattr(self, attr_name)
                id_no = attr_name.split("_")[1]
                etiket = getattr(self, f"koltukno_{id_no}", None)
                yield (buton, etiket, id_no)
            elif attr_name == "koltuktikla":
                buton = getattr(self, attr_name)
                id_no = "ozel_d4" 
                etiket = getattr(self, "koltukno", None)
                yield (buton, etiket, id_no)

    def filmleri_getir_ve_diz(self):
        hedef_alan = self.filmsecContent
        layout = self.gridLayout
        while layout.count():
            item = layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        try:
            filmler = self.filmler_table.find()
            satir, sutun = 0, 0
            MAX_SUTUN = 3 
            
            for film in filmler:
                self.kart_olustur(film, layout, satir, sutun)
                sutun += 1
                if sutun >= MAX_SUTUN:
                    sutun = 0
                    satir += 1
            layout.addItem(QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding), satir + 1, 0)
        except Exception as e:
            print(f"Film listeleme hatası: {e}")

    def kart_olustur(self, film, layout, satir, sutun):
        ad = film.get('ad', 'İsimsiz')
        fiyat = film.get('fiyat', 0)
        resim_yolu = film.get('resim', '')

        frame = QtWidgets.QFrame()
        frame.setFixedSize(160, 270)
        frame.setStyleSheet("QFrame { background-color: #2b2b2b; border-radius: 10px; border: 1px solid #444; } QFrame:hover { border: 2px solid #3498db; }")
        vbox = QtWidgets.QVBoxLayout(frame)
        vbox.setContentsMargins(5, 5, 5, 5)

        lbl_resim = QtWidgets.QLabel()
        lbl_resim.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        
        # Resim kontrolü
        if resim_yolu:
            if os.path.exists(resim_yolu):
                yol = resim_yolu
            elif os.path.exists(os.path.join(os.getcwd(), resim_yolu)):
                yol = os.path.join(os.getcwd(), resim_yolu)
            else:
                yol = None

            if yol:
                pixmap = QtGui.QPixmap(yol)
                if not pixmap.isNull():
                    lbl_resim.setPixmap(pixmap.scaled(140, 180, QtCore.Qt.AspectRatioMode.KeepAspectRatio, QtCore.Qt.TransformationMode.SmoothTransformation))
                else:
                    lbl_resim.setText("Resim Bozuk")
            else:
                 lbl_resim.setText("Resim\nBulunamadı")
        else:
            lbl_resim.setText("Resim Yok")
            
        lbl_resim.setStyleSheet("border: none;")
        vbox.addWidget(lbl_resim)

        lbl_bilgi = QtWidgets.QLabel(f"{ad}\n{fiyat} TL")
        lbl_bilgi.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        lbl_bilgi.setStyleSheet("color: white; font-weight: bold; border: none;")
        vbox.addWidget(lbl_bilgi)

        btn_sec = QtWidgets.QPushButton("SEÇ")
        btn_sec.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        btn_sec.setStyleSheet("QPushButton { background-color: #e74c3c; color: white; border-radius: 5px; font-weight: bold; padding: 5px; } QPushButton:hover { background-color: #c0392b; }")
        btn_sec.clicked.connect(lambda: self.film_secildi(ad, fiyat, resim_yolu))
        vbox.addWidget(btn_sec)

        layout.addWidget(frame, satir, sutun)

    def film_secildi(self, ad, fiyat, resim):
        self.secilen_koltuklar = []
        self.secilen_koltuk_ids = []
        self.secilen_seans = None 
        self.secilen_film = {"ad": ad, "fiyat": fiyat, "resim": resim}
        
        self.stackedWidget.setCurrentIndex(1) 
        if self.islem_turu == "satis":
            self.setWindowTitle(f"{ad} - Seans Seçimi (Satın Al)")
        else:
            self.setWindowTitle(f"{ad} - İade Edilecek Seansı Seçin")
        
        for _, objeler in self.seans_map.items():
            objeler[1].setStyleSheet(self.STYLE_FRAME_BOS)

    def seans_secildi(self, saat):
        self.secilen_seans = saat
        for s, objeler in self.seans_map.items():
            if s == saat:
                objeler[1].setStyleSheet(self.STYLE_FRAME_SECILI)
            else:
                objeler[1].setStyleSheet(self.STYLE_FRAME_BOS)
            
        satislar = self.satis_table.find({
            "film": self.secilen_film["ad"],
            "seans": saat 
        })
        
        dolu_koltuk_idleri = []
        for satis in satislar:
            if "koltuk_idleri" in satis:
                dolu_koltuk_idleri.extend(satis["koltuk_idleri"])

        for buton, etiket, id_no in self.tum_koltuklari_getir():
            buton.blockSignals(True)
            buton.setChecked(False) 
            buton.setStyleSheet("background-color: transparent; border: none;")
            
            is_dolu = (id_no in dolu_koltuk_idleri)
            
            if self.islem_turu == "satis":
                if is_dolu:
                    buton.setEnabled(False)
                    if etiket: etiket.setStyleSheet(self.STYLE_DOLU)
                else:
                    buton.setEnabled(True)
                    if etiket: etiket.setStyleSheet(self.STYLE_BOS)

            elif self.islem_turu == "iade":
                if is_dolu:
                    buton.setEnabled(True) 
                    if etiket: etiket.setStyleSheet(self.STYLE_DOLU) 
                else:
                    buton.setEnabled(False) 
                    if etiket: etiket.setStyleSheet(self.STYLE_BOS)

            buton.blockSignals(False)
        
        self.stackedWidget.setCurrentIndex(3)
        if self.islem_turu == "satis":
            self.setWindowTitle(f"Koltuk Seçimi - {saat}")
            self.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setText("Öde")
        else:
            self.setWindowTitle(f"İade Edilecek Koltukları Seçin - {saat}")
            self.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setText("İadeyi Onayla")

    def koltuklari_bagla(self):
        for buton, etiket, id_no in self.tum_koltuklari_getir():
            buton.setCheckable(True)
            if etiket:
                gercek_isim = etiket.text()
                etiket.setStyleSheet(self.STYLE_BOS)
            else:
                gercek_isim = "X"
            buton.clicked.connect(lambda checked, i=id_no, isim=gercek_isim, b=buton: self.koltuk_islem(i, isim, b))

    def koltuk_islem(self, id_no, gercek_isim, buton):
        etiket = None
        if id_no == "ozel_d4":
            etiket = getattr(self, "koltukno", None)
        else:
            etiket = getattr(self, f"koltukno_{id_no}", None)
        
        if not etiket: return

        if buton.isChecked():
            self.secilen_koltuk_ids.append(id_no)
            self.secilen_koltuklar.append(gercek_isim)
            etiket.setStyleSheet(self.STYLE_SECILI)
        else:
            if id_no in self.secilen_koltuk_ids: self.secilen_koltuk_ids.remove(id_no)
            if gercek_isim in self.secilen_koltuklar: self.secilen_koltuklar.remove(gercek_isim)
            
            if self.islem_turu == "iade":
                 etiket.setStyleSheet(self.STYLE_DOLU)
            else:
                 etiket.setStyleSheet(self.STYLE_BOS)

    def ileri_adim_kontrol(self):
        current_idx = self.stackedWidget.currentIndex()
        if current_idx == 3: 
            if not self.secilen_koltuklar:
                QtWidgets.QMessageBox.warning(self, "Uyarı", "Lütfen işlem yapılacak koltuk seçiniz!")
                return
            
            if self.islem_turu == "satis":
                toplam_koltuk = len(self.secilen_koltuklar)
                for kutu in self.kutular.values(): kutu.setValue(0)
                
                self.kutular["tam_bilet"].setMaximum(toplam_koltuk)
                self.kutular["ogrenci_bilet"].setMaximum(toplam_koltuk)

                self.stackedWidget.setCurrentIndex(2) 
                self.anlik_fiyat_hesapla()
            
            elif self.islem_turu == "iade":
                self.iade_tamamla()

        elif current_idx == 2: 
            self.satis_tamamla()

    def iade_tamamla(self):
        onay = QtWidgets.QMessageBox.question(self, "İade Onayı", 
                                              f"Seçilen Koltuklar: {', '.join(self.secilen_koltuklar)}\n\nBu biletleri iade etmek ve silmek istediğinize emin misiniz?",
                                              QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
        
        if onay == QtWidgets.QMessageBox.StandardButton.Yes:
            try:
                silinen_sayisi = 0
                for koltuk_ad in self.secilen_koltuklar:
                    filter_query = {
                        "film": self.secilen_film['ad'],
                        "seans": self.secilen_seans,
                        "koltuklar": koltuk_ad
                    }
                    update_query = { "$pull": { "koltuklar": koltuk_ad } }
                    
                    result = self.satis_table.update_one(filter_query, update_query)
                    if result.modified_count > 0:
                        silinen_sayisi += 1

                self.satis_table.delete_many({"koltuklar": {"$size": 0}})

                QtWidgets.QMessageBox.information(self, "Başarılı", f"{silinen_sayisi} adet bilet iade edildi.")
                self.giris_ekranina_don()
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Hata", f"İade hatası: {e}")

    def anlik_fiyat_hesapla(self):
        base_fiyat = self.secilen_film['fiyat']
        adet_tam = self.kutular["tam_bilet"].value()      
        adet_ogrenci = self.kutular["ogrenci_bilet"].value() 
        adet_cips = self.kutular["cips"].value()
        adet_misir = self.kutular["misir"].value()
        adet_gozluk = self.kutular["gozluk"].value()
        adet_icecek = self.kutular["icecek"].value()

        toplam_bilet = adet_tam + adet_ogrenci
        gercek_koltuk_sayisi = len(self.secilen_koltuklar)
        
        tutar_biletler = (adet_tam * base_fiyat) + (adet_ogrenci * (base_fiyat / 2))
        tutar_ekstra = (adet_cips * self.ekstra_fiyatlar["cips"]) + \
                       (adet_misir * self.ekstra_fiyatlar["misir"]) + \
                       (adet_gozluk * self.ekstra_fiyatlar["gozluk"]) + \
                       (adet_icecek * self.ekstra_fiyatlar["icecek"])
        toplam_tutar = tutar_biletler + tutar_ekstra

        btn_ok = self.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok)
        
        if toplam_bilet != gercek_koltuk_sayisi:
             btn_ok.setText(f"Adet Seç ({toplam_bilet}/{gercek_koltuk_sayisi})")
             btn_ok.setEnabled(False) 
        else:
             btn_ok.setText(f"Öde ({toplam_tutar} TL)")
             btn_ok.setEnabled(True) 
        return toplam_tutar

    def satis_tamamla(self):
        adet_tam = self.kutular["tam_bilet"].value()
        adet_ogrenci = self.kutular["ogrenci_bilet"].value()
        
        if (adet_tam + adet_ogrenci) != len(self.secilen_koltuklar):
             return 

        odenecek_tutar = self.anlik_fiyat_hesapla()
        
        ekstralar = []
        if self.kutular["cips"].value() > 0: ekstralar.append(f"{self.kutular['cips'].value()}x Cips")
        if self.kutular["misir"].value() > 0: ekstralar.append(f"{self.kutular['misir'].value()}x Mısır")
        if self.kutular["gozluk"].value() > 0: ekstralar.append(f"{self.kutular['gozluk'].value()}x Gözlük")
        if self.kutular["icecek"].value() > 0: ekstralar.append(f"{self.kutular['icecek'].value()}x İçecek")

        kayit = {
            "film": self.secilen_film['ad'],
            "seans": self.secilen_seans,
            "koltuklar": self.secilen_koltuklar,
            "koltuk_idleri": self.secilen_koltuk_ids,
            "bilet_detay": {"tam": adet_tam, "ogrenci": adet_ogrenci},
            "ekstralar": ekstralar,
            "toplam_odenen": odenecek_tutar,
            "tarih": QtCore.QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss")
        }

        try:
            self.satis_table.insert_one(kayit)
            QtWidgets.QMessageBox.information(self, "Başarılı", 
                                              f"İşlem Tamamlandı!\n\n"
                                              f"Film: {self.secilen_film['ad']}\n"
                                              f"Seans: {self.secilen_seans}\n"
                                              f"Koltuklar: {self.secilen_koltuklar}\n"
                                              f"Tutar: {odenecek_tutar} TL")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Hata", f"Veritabanı kaydı hatası: {e}")
        
        self.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setText("OK")
        self.giris_ekranina_don()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    pencere = SinemaUygulamasi()
    pencere.show()
    sys.exit(app.exec())