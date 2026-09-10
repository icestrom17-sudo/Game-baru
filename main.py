import traceback

from kivy.app import App
from kivy.base import ExceptionHandler, ExceptionManager
from kivy.core.window import Window
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView

from game import DarkKnightGame


class CrashHandler(ExceptionHandler):
    def handle_exception(self, inst):
        error_text = traceback.format_exc()
        print(error_text)

        try:
            label = Label(
                text=error_text,
                color=(1, 0.3, 0.3, 1),
                font_size="14sp",
                size_hint=(None, None),
                text_size=(Window.width - 40, None),
                halign="left",
                valign="top",
                padding=(20, 20),
            )
            label.bind(texture_size=lambda *_: setattr(label, "size", label.texture_size))

            scroll = ScrollView(size_hint=(1, 1))
            scroll.add_widget(label)

            Window.clear()
            for child in list(Window.children):
                Window.remove_widget(child)
            Window.add_widget(scroll)
        except Exception:
            pass

        return ExceptionManager.PASS


ExceptionManager.add_handler(CrashHandler())


class DarkKnightApp(App):
    def build(self):
        self.title = "Dark Knight: Revenge of Light"
        return DarkKnightGame()


if __name__ == "__main__":
    DarkKnightApp().run()
