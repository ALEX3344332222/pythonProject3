from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, APIC

def extract_metadata(file_path):
    try:
        # Загружаем аудиофайл
        audio = MP3(file_path, ID3=ID3)

        # Извлекаем метаданные
        title = audio.get('TIT2', 'Unknown Title').text[0] if audio.get('TIT2') else 'Unknown Title'
        artist = audio.get('TPE1', 'Unknown Artist').text[0] if audio.get('TPE1') else 'Unknown Artist'
        album = audio.get('TALB', 'Unknown Album').text[0] if audio.get('TALB') else 'Unknown Album'
        genre = audio.get('TCON', 'Unknown Genre').text[0] if audio.get('TCON') else 'Unknown Genre'
        year = audio.get('TDRC', 'Unknown Year').text[0] if audio.get('TDRC') else 'Unknown Year'

        # Извлекаем картинку трека
        apic = audio.get('APIC:')
        if apic:
            image_path = f"{file_path}.jpg"
            with open(image_path, "wb") as img_file:
                img_file.write(apic.data)
            image_info = f"Image saved to {image_path}"
        else:
            image_info = "No image found"

        # Выводим метаданные в консоль
        print(f"Title: {title}")
        print(f"Artist: {artist}")
        print(f"Album: {album}")
        print(f"Genre: {genre}")
        print(f"Year: {year}")
        print(image_info)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    file_path = input("Enter the path to the audio file: ")
    extract_metadata(file_path)
