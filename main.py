# --Importar bibliotecas--
import cv2
import speech_recognition as sr
import requests
import pywhatkit
import threading
import numpy as np
import base64
import json
import datetime
import locale
import random
import requests
import os
from PIL import Image
from openai import OpenAI
from gtts import gTTS
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.core.window import Window
from kivy.core.audio import SoundLoader
class MainApp(MDApp):
                          
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        threading.Thread(target=self.reconocer_voz).start()
        self.DijoHyo = False
        self.recording = True
        
    def build(self):
        layout = MDBoxLayout(orientation='vertical', size_hint=(1, 1))
        self.image = Image(size_hint=(1, 1), allow_stretch=True, keep_ratio=False)
        layout.add_widget(self.image)

        self.capture = cv2.VideoCapture(0)
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 960)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.original_frame_size = (self.capture.get(cv2.CAP_PROP_FRAME_WIDTH), self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT))

        Clock.schedule_interval(self.load_video, 1.0 / 30.0)
        Window.bind(on_resize=self.update_window_size)
        return layout
    
    def update_window_size(self, instance, width, height):
        # Esta función se llama cada vez que la ventana se redimensiona
        print(f"Nuevas dimensiones de la ventana: {width} x {height}")
        
    def load_video(self, *args):
        ret, frame = self.capture.read()
        self.image_frame = frame
        buffer = cv2.flip(frame, 0).tostring()
        texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
        texture.blit_buffer(buffer, colorfmt='bgr', bufferfmt='ubyte')
        self.image.texture = texture
    
    #--Cargar la api key de OpenAI
    client = OpenAI(api_key="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")
    
    def obtener_ciudad_actual(self):
        url = 'https://ipinfo.io/json'
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            ciudad = data.get('city', 'Desconocido')
            clima = self.ClimaActual(ciudad)
            clima = clima + "Puede que la ubicación no sea exacta porque es complicado para mí obtenerla. Si desea el clima de una ciudad en específico solo di: Dime el clima de X ciudad"
            return clima
        else:
            return 'No se pudo obtener la ubicación actual'

    def ClimaActual(self, ciudad):
        url = f"https://es.wttr.in/{ciudad}?format=j1"
        response = requests.get(url)
        weather_dic = response.json()
        temp_c = weather_dic["current_condition"][0]['temp_C']
        desc_temp = weather_dic["current_condition"][0]['lang_es']
        desc_temp = desc_temp[0]['value']
        Clima = (f"El clima actual de{ciudad} es {temp_c} °C {desc_temp}.")
        return Clima

    def leerRespuesta(self, TextoALeer):
        tts = gTTS(text=TextoALeer, lang='es', slow=False)
        tts.save("audio.mp3")
        self.ReproducirAudio("audio")      

    def ReproducirAudio(self, AudioNombre):
        print("Entro a reproducir audio funcion")
        sound = SoundLoader.load(f"{AudioNombre}.mp3")
        if sound:
            sound.play()
            sound_length = sound.get_length()
    
    #-- Función para codificar la imagen para GPT-4
    def encode_image(self, image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def HYOVision(self, TextoADescribir):
            cv2.imwrite("foto.png", self.image_frame)
            sound = SoundLoader.load("camara.mp3")
            sound.play()
            image_path = "foto.png"
            base64_image = self.encode_image(image_path)
            api_key = "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"
            headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
            }

            payload = {
            "model": "gpt-4-vision-preview",
            "messages": [
                {
                "role": "assistant",
                "content": [
                    {
                    "type": "text",
                    "text": TextoADescribir
                    },
                    {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}"
                    }
                    }
                ]
                }
            ],
            "max_tokens": 200
            }

            response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)

                # Verificar si la solicitud fue exitosa
            if response.status_code == 200:
                    print("Entro al if Response HYO-VISION")
                    data = json.loads(response.content)
                    respuesta = data['choices'][0]['message']['content']
                    self.leerRespuesta(respuesta)
            else:
                    print(f"Error: {response.status_code}")

    def reconocer_voz(self):
        try:
            recognizer = sr.Recognizer() # Se inicializan el reconocedor de voz
            mic = sr.Microphone() # Se inicializan el microfono
            with mic as source:
                print("Microfono Activo")
                if self.recording:
                    audio = recognizer.listen(source)
                    text = recognizer.recognize_google(audio, language='ES')
                    print(f"Has dicho : {text}")
                    text = text.lower()

            if self.DijoHyo == False:
                print("Entro al if hyo false")
                if ("oye io" == text) or ("oye yo" == text) or ("oye tío" == text) or ("oye hijo" == text):
                    print("Entro al if si dijo io")
                    self.DijoHyo = True
                    RandomNum = random.randint(1, 2)
                    self.ReproducirAudio(f"Escuchando{RandomNum}")
                    self.recording = False  # Detener la grabación
                threading.Thread(target=self.reconocer_voz).start()              
            else:
                self.DijoHyo = False
                self.recording = True
                if ("preséntate" in text) or ("hola" in text):
                    print("Entro al if presentacion")
                    self.ReproducirAudio("Presentacion")
                    
                elif "qué es el cetis 108" in text:
                    print("Entro al if CETis108")
                    self.ReproducirAudio("CETis108")
            
                elif ("dime el clima de" in text) or ("dime el clima en" in text) or ("dime la temperatura de" in text) or ("la temperatura en" in text):
                    if "dime el clima de" in text:
                        TextoAQuitar = "dime el clima de"
                    elif "dime el clima en" in text:
                        TextoAQuitar = "dime el clima en"
                    elif "dime la temperatura de" in text:
                        TextoAQuitar = "dime la temperatura de"
                    elif "dime la temperatura en" in text:
                        TextoAQuitar = "dime la temperatura en"
                    ciudad = text.replace(TextoAQuitar, "")
                    clima = self.ClimaActual(ciudad)
                    print(clima)
                    self.leerRespuesta(clima)
            
                elif ("reproduce" in text) or ("pon" in text):
                    if "reproduce" in text:
                        TextoAQuitar = "reproduce"
                    else:
                        TextoAQuitar = "pon"    
                    cancion = text.replace(TextoAQuitar, "")
                    try:
                        pywhatkit.playonyt(cancion)
                        self.leerRespuesta("Reproduciendo " + cancion)
                    except ValueError as e:
                        self.ReproducirAudio("Error1")
            
                elif ("hora es" in text) or ("horas son" in text):
                    MinutosActualSinFormato = datetime.datetime.strftime(datetime.datetime.now(), '%M')
                    MinutosActualSinFormato = int(MinutosActualSinFormato)
                    HoraActualSinFormato = datetime.datetime.strftime(datetime.datetime.now(), '%H')
                    HoraActualSinFormato = int(HoraActualSinFormato)
                    if HoraActualSinFormato <= 12:
                        if HoraActualSinFormato == 1:
                            ComplementoHora = "son la 1 de la mañana"
                        else:
                            ComplementoHora = f"son las {HoraActualSinFormato} de la mañana"
                    else:
                        HoraActualSinFormato = HoraActualSinFormato-12
                        if HoraActualSinFormato == 1:
                            ComplementoHora = "son la 1 de la tarde"
                        elif (HoraActualSinFormato > 1) and (HoraActualSinFormato < 8):
                            ComplementoHora = f"son las {HoraActualSinFormato} de la tarde"
                        else:
                            ComplementoHora = f"son las {HoraActualSinFormato} de la noche"
                            
                    if MinutosActualSinFormato == 1:
                        ComplementoMinuto = "con 1 minuto"
                    else:
                        ComplementoMinuto = f"con {MinutosActualSinFormato} minutos"
                        
                    HoraActual = f"{ComplementoHora} {ComplementoMinuto}"
                    self.leerRespuesta(HoraActual)
            
                elif ("qué día es hoy" in text):
                    locale.setlocale(locale.LC_TIME, 'es_ES')
                    FechaActual = datetime.datetime.strftime(datetime.datetime.now(), f'Hoy es %A %d de %B del %Y')
                    self.leerRespuesta(FechaActual)
            
                elif("qué miras" in text) or ("qué observas" in text) or ("qué dice aquí" in text):
                    print("Entro a HYO Vision")
                    self.HYOVision(text)
                
                else:
                    print("Entro a GPT-3.5 TURBO")
                    completion = self.client.chat.completions.create(
                        messages=[
                            {
                                "role": "assistant",
                                "content": text+"(La respuesta tiene que estar en español)",
                            }
                        ],
                        model="gpt-3.5-turbo",
                    )
                    print(completion.choices[0].message.content)
                    self.leerRespuesta(completion.choices[0].message.content)
        except Exception as e:
            print(f"Error: {e}")
            threading.Thread(target=self.reconocer_voz).start()

if __name__ == '__main__':
    MainApp().run()