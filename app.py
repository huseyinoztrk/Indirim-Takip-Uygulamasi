from os import close
from typing import List
from sqlalchemy import create_engine, ForeignKey, Column, Integer, String
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import requests
from lxml import html
from sqlalchemy.sql.expression import false, true
from win10toast import ToastNotifier
import tkinter as tk
import threading
import time
import PIL.Image
import PIL.ImageTk
engine = create_engine('sqlite:///database.db?check_same_thread=False')
Base = declarative_base()

class App(Base):
   __tablename__ = 'apps'
   id = Column(Integer, primary_key=True)
   name = Column(String)
   url = Column(String)
   xpProductName = Column(String)
   xpProductPrice = Column(String)

class Product(Base):
   __tablename__ = 'products'
   id = Column(Integer, primary_key=True)
   name = Column(String)
   url = Column(String)
   priceFirst = Column(Integer)
   priceNow = Column(Integer)
   appId = Column(Integer, ForeignKey('apps.id'))
   app = relationship("App", back_populates = "products")

class Notification(Base):
   __tablename__ = 'notifications'
   id = Column(Integer, primary_key=True)
   notification = Column(String)

App.products = relationship("Product", order_by = Product.id, back_populates = "app")

Base.metadata.create_all(engine)

Session = sessionmaker(bind = engine)
session = Session()

result = session.query(App).all()

def getPageContent(url):
   page = requests.get(url)
   return html.fromstring(page.content)

def getProductInfo(url, xp):
   tree = getPageContent(url)
   info = tree.xpath(xp)
   return str(info[0].strip())

root=tk.Tk(className="Online Alisveris Takip")
root.resizable(0, 0)
entryUrlText=tk.StringVar()

def updateListbox():
   try:
      productsListBox.delete(0,tk.END)
   except:
      pass
   result = session.query(Product).all()
   for row in result:
      strC =  (str(row.id) + ". Ürün Adı: " + row.name[:16] + "..., İlk Fiyat: " + str(row.priceFirst) + ", Son Fiyat: " + str(row.priceNow) )
      productsListBox.insert(productsListBox.size(), strC)

def updateNot(): 
   result = session.query(Product).all()
   for row in result:
      if(int(row.priceNow) < int(row.priceFirst)):
         strC = (str(row.id) + " numaralı ürünün fiyatı " + str(row.priceFirst) + "'ten " + str(row.priceNow) + "a' düştü!")
         notListBox.insert(notListBox.size(), strC)
         toaster = ToastNotifier()
         toaster.show_toast("İndirim Bildirimi",
         strC,
         duration=10)
         newNt = Notification(notification=strC)
         row.priceFirst = row.priceNow
         session.add(row)
         session.add(newNt)
         session.commit()

def updateProducts():
   result = session.query(Product).all()
   for row in result:
      result2 = session.query(App).filter(App.url.like( row.url[:15] + "%" ))
      for row2 in result2:
         row.priceNow = int(getProductInfo(row.url, row2.xpProductPrice).split(",")[0].replace(".",""))
         session.add(row)
         session.commit()
         break
   updateListbox()

def addUrl():
   result = session.query(App).filter(App.url.like( entryUrlText.get()[:15] + "%" ) )
   for row in result:
      row.products = [Product(name = getProductInfo(entryUrlText.get(), row.xpProductName), url = entryUrlText.get(), priceFirst = int(getProductInfo(entryUrlText.get(), row.xpProductPrice).split(",")[0].replace(".","")), priceNow = int(getProductInfo(entryUrlText.get(), row.xpProductPrice).split(",")[0].replace(".","")) )]
      session.add(row)
      session.commit()
      break
   updateListbox()

def deleteProduct():
   sel = productsListBox.curselection()
   itemId = productsListBox.get(sel)[:3]
   itemId = int(''.join(filter(str.isdigit, itemId)))
   productsListBox.delete(sel)
   selectedProduct = session.query(Product).get(itemId)
   session.delete(selectedProduct)
   session.commit()

def deleteNot():
   sel = notListBox.curselection()
   itemId = notListBox.get(sel)[:3]
   itemId = int(''.join(filter(str.isdigit, itemId)))
   notListBox.delete(sel)
   selectedNot = session.query(Notification).get(itemId)
   session.delete(selectedNot)
   session.commit()

def autoUpdate(threadName):
   try:
      while(runThread):
         updateProducts()
         updateNot()
         time.sleep(10)
   except:
      pass

def closeApp():
   root.destroy()
   session.close()
   runThread = false

runThread = True
t1 = threading.Thread(target=autoUpdate, args = ("thread-1", ))
t1.start()

img = PIL.Image.open("logo.png")
img1 = PIL.ImageTk.PhotoImage(img)

tk.Label(root, image = img1).grid(column=0, row = 0, pady=50, padx=25, columnspan=4)

tk.Label(root, text="Ürün URL: ", font=("Consolas", 16)).grid(column=0, row=1)
entryUrl = tk.Entry(root,textvariable = entryUrlText, font=("Consolas", 16), width=50)
entryUrl.grid(column=1, row=1)

buttonAddUrl = tk.Button(root, text="Ürün Ekle", command=addUrl, fg="white", background="orange", font=("Arial", 14))
buttonAddUrl.grid(column=2, row=1)

buttonDeleteProduct = tk.Button(root, text="Ürün Sil", command=deleteProduct, fg="white", background="red", font=("Arial", 14))
buttonDeleteProduct.grid(column=3, row=1)

tk.Label(root, text="Takip Edilen Ürünler", font=("Consolas", 16)).grid(column=0, row=2, columnspan=4)
productsListBox = tk.Listbox(root, font=("Consolas", 14), width=100)
productsListBox.grid(column = 0, row = 3, columnspan=4, pady=10)

tk.Label(root, text="İndirim Bildirimleri", font=("Consolas", 16)).grid(column=0, row=4, columnspan=4)
notListBox = tk.Listbox(root, width=100)
notListBox.grid(column = 0, row = 5, columnspan=4, pady=10)

buttonClear = tk.Button(root, text="Bildirim Sil", command=deleteNot, fg="white", background="red", font=("Arial", 14))
buttonClear.grid(column=0, row=6, columnspan=4)

buttonExit = tk.Button(root, text="Çıkış", command=closeApp, font=("Arial", 14), fg="white", background="black")
buttonExit.grid(column=0, row=7, columnspan=4, pady=10)

root.mainloop()

session.close()
