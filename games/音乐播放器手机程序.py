from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.listview import ListView, ListItemButton
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.popup import Popup
from kivy.core.audio import SoundLoader
import os
import glob
import pyttsx3

class MusicPlayerApp(App):
    def build(self):
        self.engine = pyttsx3.init()
        self.sound = None
        self.current_index = 0
        self.music_list = []

        layout = BoxLayout(orientation='vertical')

        self.file_chooser_popup = Popup(title='选择文件夹', content=FileChooserListView(), size_hint=(0.9, 0.9))
        self.file_chooser_popup.content.bind(on_selection_change=self.on_folder_select)

        self.scan_button = Button(text='扫描文件夹')
        self.scan_button.bind(on_press=self.show_file_chooser)
        layout.add_widget(self.scan_button)

        self.song_label = Label(text='', size_hint_y=None, height=50)
        layout.add_widget(self.song_label)

        self.list_view = ListView(item_strings=[], item_class=ListItemButton)
        self.list_view.adapter.data = []
        self.list_view.adapter.bind(on_selection_change=self.on_song_select)
        layout.add_widget(self.list_view)

        control_layout = BoxLayout(size_hint_y=None, height=100)
        self.prev_button = Button(text='上一首')
        self.prev_button.bind(on_press=self.play_prev_song)
        control_layout.add_widget(self.prev_button)

        self.play_button = Button(text='播放')
        self.play_button.bind(on_press=self.toggle_play)
        control_layout.add_widget(self.play_button)

        self.next_button = Button(text='下一首')
        self.next_button.bind(on_press=self.play_next_song)
        control_layout.add_widget(self.next_button)

        layout.add_widget(control_layout)

        return layout

    def show_file_chooser(self, instance):
        self.file_chooser_popup.open()

    def on_folder_select(self, instance):
        folder_path = instance.selection and instance.selection[0] or ''
        if folder_path:
            self.scan_music_files(folder_path)
            self.file_chooser_popup.dismiss()

    def scan_music_files(self, folder_path):
        music_files = glob.glob(os.path.join(folder_path, '**/*.mp3'), recursive=True) + \
                      glob.glob(os.path.join(folder_path, '**/*.wav'), recursive=True)
        self.music_list = sorted(music_files)
        self.update_list_view()

    def update_list_view(self):
        self.list_view.adapter.data = self.music_list
        self.list_view._trigger_reset_populate()

    def on_song_select(self, adapter):
        selection = adapter.selection
        if selection:
            self.current_index = self.music_list.index(selection[0].text)
            self.play_current_song()

    def play_current_song(self):
        if self.sound:
            self.sound.stop()
        song_path = self.music_list[self.current_index]
        self.song_label.text = f'正在播放: {os.path.basename(song_path)}'
        self.speak_text(os.path.basename(song_path))
        self.sound = SoundLoader.load(song_path)
        if self.sound:
            self.sound.play()

    def speak_text(self, text):
        self.engine.say(text)
        self.engine.runAndWait()

    def toggle_play(self, instance):
        if self.sound:
            if self.sound.state == 'play':
                self.sound.stop()
                instance.text = '播放'
            else:
                self.sound.play()
                instance.text = '暂停'

    def play_next_song(self, instance):
        if self.current_index < len(self.music_list) - 1:
            self.current_index += 1
            self.play_current_song()

    def play_prev_song(self, instance):
        if self.current_index > 0:
            self.current_index -= 1
            self.play_current_song()

if __name__ == '__main__':
    MusicPlayerApp().run()



