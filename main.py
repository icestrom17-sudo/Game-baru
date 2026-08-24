from kivy.app import App
from game import DarkKnightGame

class DarkKnightApp(App):
    def build(self):
        self.title = "Dark Knight: Revenge of Light"
        return DarkKnightGame()

if __name__ == '__main__':
    DarkKnightApp().run()

