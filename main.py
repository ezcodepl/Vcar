from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QFileDialog, QVBoxLayout,
                             QHBoxLayout, QWidget, QLabel, QListWidget, QListWidgetItem, QSlider, QFrame,
                             QSizePolicy, QScrollArea)
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtGui import QIcon
import sys
import os


class VideoPlayerApp(QMainWindow):
    def __init__(self):
        super().__init__()

        # Główne okno
        self.setWindowTitle("Video Player with GPS and Telemetry")
        self.setGeometry(0, 0, 1500, 1000)

        # Layout główny
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        # Layout poziomy dla wideo po lewej i listy plików po prawej
        self.content_layout = QHBoxLayout()

        # Sekcja odtwarzania wideo (po lewej stronie) - dodajemy ramkę wokół wideo
        self.video_frame = QFrame(self)
        self.video_frame.setFrameShape(QFrame.Box)  # Ramka wokół wideo
        self.video_frame.setFrameShadow(QFrame.Sunken)  # Cień dla ramki

        # Layout dla widgetu wideo w ramce
        self.video_layout = QVBoxLayout(self.video_frame)

        # Tworzymy QScrollArea do osadzenia wideo w przewijalnym obszarze
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)  # Pozwól na elastyczne rozciąganie widgetu
        self.scroll_area.setWidget(self.video_frame)

        # Widget wideo
        self.video_widget = QVideoWidget(self)
        self.video_layout.addWidget(self.video_widget)

        # Ustawiamy politykę rozmiaru dla wideo, aby elastycznie się skalowało
        self.video_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Dodajemy scroll area do głównego układu
        self.content_layout.addWidget(self.scroll_area)

        # Layout dla przycisków i listy plików (po prawej stronie)
        self.file_layout = QVBoxLayout()

        # Przycisk "Wczytaj plik"
        self.load_file_button = QPushButton("Wczytaj plik", self)
        self.load_file_button.clicked.connect(self.load_file)
        self.file_layout.addWidget(self.load_file_button)

        # Przycisk "Wczytaj folder"
        self.load_folder_button = QPushButton("Wczytaj folder", self)
        self.load_folder_button.clicked.connect(self.load_folder)
        self.file_layout.addWidget(self.load_folder_button)

        # Sekcja listy plików (po prawej stronie)
        self.file_list_widget = QListWidget(self)
        self.file_list_widget.setFixedWidth(300)
        self.file_list_widget.itemClicked.connect(self.play_selected_video)  # Obsługa kliknięcia na element listy
        self.file_layout.addWidget(self.file_list_widget)

        # Dodajemy układ z przyciskami i listą plików do układu poziomego
        self.content_layout.addLayout(self.file_layout)

        # Dodajemy układ poziomy do głównego layoutu
        self.main_layout.addLayout(self.content_layout)

        # Pasek postępu pod oknem wideo
        self.position_slider = QSlider(Qt.Horizontal, self)
        self.position_slider.setRange(0, 0)
        self.position_slider.sliderMoved.connect(self.set_position)
        self.main_layout.addWidget(self.position_slider)

        # Layout na przyciski sterujące (pod paskiem postępu)
        self.controls_layout = QHBoxLayout()

        # Przyciski: Poprzedni, Stop, Play, Pause, Następny
        self.prev_button = QPushButton("⏮", self)
        self.prev_button.setStyleSheet("font-size: 30px;")
        self.prev_button.clicked.connect(self.prev_video)
        self.controls_layout.addWidget(self.prev_button)

        self.stop_button = QPushButton("⏹", self)
        self.stop_button.setStyleSheet("font-size: 30px;")
        self.stop_button.clicked.connect(self.stop_video)
        self.controls_layout.addWidget(self.stop_button)

        self.play_button = QPushButton("⏵", self)
        self.play_button.setStyleSheet("font-size: 30px;")
        self.play_button.clicked.connect(self.play_video)
        self.controls_layout.addWidget(self.play_button)

        self.pause_button = QPushButton("⏸", self)
        self.pause_button.setStyleSheet("font-size: 30px;")
        self.pause_button.clicked.connect(self.pause_video)
        self.controls_layout.addWidget(self.pause_button)

        self.next_button = QPushButton("⏭", self)
        self.next_button.setStyleSheet("font-size: 30px;")
        self.next_button.clicked.connect(self.next_video)
        self.controls_layout.addWidget(self.next_button)

        # Dodajemy przyciski sterujące pod wideo
        self.main_layout.addLayout(self.controls_layout)

        # Suwak głośności
        self.volume_slider = QSlider(Qt.Horizontal, self)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)  # Ustawiamy początkowy poziom głośności na 50%
        self.volume_slider.valueChanged.connect(self.set_volume)
        self.controls_layout.addWidget(self.volume_slider)

        # Etykieta dla suwaka głośności
        self.volume_label = QLabel("Głośność: 50%", self)
        self.volume_slider.valueChanged.connect(self.update_volume_label)
        self.controls_layout.addWidget(self.volume_label)

        # Przyciski powiększania/zmniejszania obrazu
        self.zoom_in_button = QPushButton("🔍+", self)
        self.zoom_in_button.clicked.connect(self.zoom_in)
        self.controls_layout.addWidget(self.zoom_in_button)

        self.zoom_out_button = QPushButton("🔍-", self)
        self.zoom_out_button.clicked.connect(self.zoom_out)
        self.controls_layout.addWidget(self.zoom_out_button)

        # MediaPlayer dla odtwarzacza wideo
        self.media_player = QMediaPlayer(self)
        self.media_player.setVideoOutput(self.video_widget)
        self.media_player.positionChanged.connect(self.position_changed)
        self.media_player.durationChanged.connect(self.duration_changed)

        # Zmienna do przechowywania ścieżek do plików
        self.file_paths = []
        self.current_video_index = -1  # Indeks aktualnie odtwarzowanego pliku

    def load_file(self):
        """Funkcja do wczytywania pojedynczego pliku."""
        file_dialog = QFileDialog(self)
        file_path, _ = file_dialog.getOpenFileName(self, "Wybierz plik wideo", "", "MP4 Files (*.mp4)")
        if file_path:
            self.file_paths = [file_path]  # Zapisujemy tylko jeden plik
            self.update_file_list()  # Aktualizujemy listę plików
            self.current_video_index = 0  # Resetujemy indeks wideo
            self.play_selected_video()

    def load_folder(self):
        """Funkcja do wczytywania wszystkich plików MP4 z wybranego folderu."""
        folder_dialog = QFileDialog(self)
        folder_path = folder_dialog.getExistingDirectory(self, "Wybierz folder")
        if folder_path:
            # Wyszukujemy wszystkie pliki MP4 w folderze
            self.file_paths = []
            for file_name in os.listdir(folder_path):
                if file_name.lower().endswith(".mp4"):
                    self.file_paths.append(os.path.join(folder_path, file_name))
            self.update_file_list()  # Aktualizujemy listę plików
            self.current_video_index = 0  # Resetujemy indeks wideo

    def update_file_list(self):
        """Funkcja aktualizująca listę plików w interfejsie."""
        self.file_list_widget.clear()  # Czyszczenie listy przed wczytaniem nowych plików
        for idx, file_path in enumerate(self.file_paths):
            file_name = os.path.basename(file_path)  # Nazwa pliku bez ścieżki
            list_item = QListWidgetItem(f"{idx + 1}. {file_name}")  # Numerujemy pliki na liście
            self.file_list_widget.addItem(list_item)

    def play_selected_video(self):
        """Odtwarzanie wybranego pliku wideo po kliknięciu w liście."""
        if self.current_video_index >= 0 and self.current_video_index < len(self.file_paths):
            file_path = self.file_paths[self.current_video_index]
            self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(file_path)))
            self.media_player.play()

    def play_video(self):
        """Odtwarza aktualnie załadowane wideo."""
        self.media_player.play()

    def pause_video(self):
        """Pauzuje aktualnie odtwarzowane wideo."""
        self.media_player.pause()

    def stop_video(self):
        """Zatrzymuje odtwarzanie wideo."""
        self.media_player.stop()

    def next_video(self):
        """Przełącza na następne wideo w liście."""
        if self.current_video_index < len(self.file_paths) - 1:
            self.current_video_index += 1
            self.play_selected_video()

    def prev_video(self):
        """Przełącza na poprzednie wideo w liście."""
        if self.current_video_index > 0:
            self.current_video_index -= 1
            self.play_selected_video()

    def set_position(self, position):
        """Zmienia pozycję odtwarzania na pasku postępu."""
        self.media_player.setPosition(position)

    def position_changed(self, position):
        """Aktualizuje pasek postępu w trakcie odtwarzania."""
        self.position_slider.setValue(position)

    def duration_changed(self, duration):
        """Ustawia maksymalną wartość paska postępu."""
        self.position_slider.setRange(0, duration)

    def set_volume(self, volume):
        """Zmienia poziom głośności."""
        self.media_player.setVolume(volume)

    def update_volume_label(self):
        """Aktualizuje etykietę głośności przy suwaku."""
        volume_value = self.volume_slider.value()
        self.volume_label.setText(f"Głośność: {volume_value}%")

    def zoom_in(self):
        """Powiększa wideo o 10%."""
        self.zoom_video(10)

    def zoom_out(self):
        """Zmniejsza wideo o 10%."""
        self.zoom_video(-10)

    def zoom_video(self, zoom_delta):
        """Zmienia wielkość okna wideo w przewijalnym obszarze."""
        current_width = self.video_widget.width()
        current_height = self.video_widget.height()
        new_width = current_width + zoom_delta * 9  # Zmiana szerokości o 10%
        new_height = current_height + zoom_delta * 6  # Zmiana wysokości o 10%
        # Ograniczamy minimalne i maksymalne rozmiary
        new_width = max(450, min(new_width, 3800))
        new_height = max(300, min(new_height, 2400))
        self.video_widget.setFixedWidth(new_width)
        self.video_widget.setFixedHeight(new_height)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    player = VideoPlayerApp()
    player.show()
    sys.exit(app.exec_())
