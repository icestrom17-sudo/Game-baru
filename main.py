from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label

class GameInteraktif(App):
    def build(self):
        self.score = 0
        
        # Layout utama aplikasi
        layout = BoxLayout(orientation='vertical', padding=40, spacing=20)
        
        # Teks / Label di layar
        self.label = Label(text='Selamat Datang di Game-mu!\nTekan tombol di bawah:', font_size=24, halign='center')
        layout.add_widget(self.label)
        
        # Tombol interaktif yang bisa diklik
        btn = Button(text='KLIK AKU!', font_size=28, background_color=(0.1, 0.6, 1, 1))
        btn.bind(on_press=self.tambah_skor)
        layout.add_widget(btn)
        
        return layout

    def tambah_skor(self, instance):
        self.score += 1
        self.label.text = f'Skor Kamu: {self.score}\nKeren, terus klik!'

if __name__ == '__main__':
    GameInteraktif().run()
