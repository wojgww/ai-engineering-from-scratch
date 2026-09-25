# Niezbędne komendy Docker dla środowiska bez karty NVIDIA (CPU)
> Na podstawie lekcji: `phases/00-setup-and-tooling/07-docker-for-ai`
> Środowisko: **Ubuntu 24.04 LTS | Procesor Intel (bez dedykowanej karty NVIDIA)**

Poniższy zestaw komend to kompletny przewodnik po lekcji Dockera z tego repozytorium, przystosowany w 100% do pracy na Twoim procesorze (z wyciętymi flagami `--gpus` i zbędnymi zależnościami CUDA).

---

## 1. Weryfikacja instalacji i uprawnień (Krok 1)

Upewnij się, że Docker działa bez uprawnień roota (`sudo`):

```bash
# Przypisanie użytkownika do grupy docker (wykonane jednorazowo)
sudo usermod -aG docker $USER

# Przeładowanie uprawnień w bieżącym terminalu (lub przeloguj się)
newgrp docker

# Weryfikacja wersji Dockera
docker --version

# Test działania Dockera
docker run hello-world
```

---

## 2. Krok 2 z kursu: Instalacja NVIDIA Container Toolkit

> ⚠️ **KROK POMIJANY**: W Twoim komputerze działa układ **Intel Iris Xe Graphics**. Nie instalujesz `nvidia-container-toolkit`, a w żadnym kolejnym poleceniu **nie używasz flagi `--gpus all`**. Kontenery automatycznie wykorzystają pełną moc procesora.

---

## 3. Budowanie obrazu Docker (Krok 4)

Upewnij się, że jesteś w katalogu `without_nvdia_gpu`, gdzie znajduje się Twój dostosowany `Dockerfile`:

```bash
cd /home/ai_workspace/Projekty/ai-engineering-from-scratch/without_nvdia_gpu

# Budowanie obrazu z tagiem 'ai-dev-cpu'
docker build -t ai-dev-cpu .
```

*Wskazówka:* Dzięki wersji CPU obraz zbuduje się znacznie szybciej i zajmie o kilka gigabajtów mniej miejsca na dysku niż wersja z CUDA.

---

## 4. Uruchamianie kontenera z PyTorch (Krok 4)

### A. Szybki test działania PyTorch na CPU
```bash
docker run --rm -it \
    -v $(pwd):/workspace \
    -v ~/models:/models \
    ai-dev-cpu python -c "import torch; print(f'PyTorch {torch.__version__} | CUDA dostepna: {torch.cuda.is_available()}')"
```
*Oczekiwany wynik:* `CUDA dostepna: False` — PyTorch zgłosi gotowość do pracy w trybie CPU.

### B. Uruchomienie interaktywnej powłoki Bash wewnątrz kontenera
```bash
docker run --rm -it \
    -v $(pwd):/workspace \
    -v ~/models:/models \
    ai-dev-cpu bash
```

### C. Uruchomienie serwera Jupyter Notebook
```bash
docker run --rm -it \
    -v $(pwd):/workspace \
    -v ~/models:/models \
    -p 8888:8888 \
    ai-dev-cpu jupyter notebook --ip=0.0.0.0 --port=8888 --no-browser --allow-root
```
*Po uruchomieniu skopiuj link z terminala (z tokenem `http://127.0.0.1:8888/tree?token=...`) i wklej w przeglądarce.*

---

## 5. Montowanie wolumenów dla modeli i danych (Krok 5)

Aby pobierane modele i dane nie znikały po wyłączeniu kontenera, zawsze montujemy katalogi z dysku komputera:

* `-v $(pwd):/workspace` — bieżący kod projektu
* `-v ~/models:/models` — wagi modeli (np. z HuggingFace)
* `-v ~/datasets:/data` — zbiory danych

Przykład uruchomienia z pełnym zestawem wolumenów:
```bash
docker run --rm -it \
  -v $(pwd):/workspace \
  -v ~/models:/models \
  -v ~/datasets:/data \
  -p 8888:8888 \
  ai-dev-cpu bash
```

---

## 6. Docker Compose dla wielu usług (Krok 6)

Dla aplikacji AI (np. kontener AI + wektorowa baza danych **Qdrant**), zamiast oryginalnego pliku z rezerwacją GPU, używasz konfiguracji CPU:

### Zawartość `docker-compose.yml` (wersja CPU):
```yaml
services:
  ai-dev:
    build:
      context: .
      dockerfile: Dockerfile
    volumes:
      - .:/workspace
      - ~/models:/models
      - ~/datasets:/data
    ports:
      - "8888:8888"
    stdin_open: true
    tty: true
    command: jupyter notebook --ip=0.0.0.0 --port=8888 --no-browser --allow-root

  qdrant:
    image: qdrant/qdrant:v1.12.5
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - qdrant_data:/qdrant/storage

volumes:
  qdrant_data:
```

### Komendy zarządzania stosem:
```bash
# Uruchomienie w tle (kontener AI + baza Qdrant)
docker compose up -d

# Podgląd statusu uruchomionych serwisów
docker compose ps

# Podgląd logów na żywo
docker compose logs -f

# Zatrzymanie kontenerów (dane Qdrant zostają zachowane)
docker compose down

# Zatrzymanie z usunięciem danych wektorowych Qdrant
docker compose down -v
```

---

## 7. Podręczne komendy do zarządzania Dockerem (Krok 7)

```bash
# Lista aktualnie uruchomionych kontenerów
docker ps

# Lista wszystkich kontenerów (również zatrzymanych)
docker ps -a

# Lista pobranych obrazów i ich rozmiary
docker images

# Wejście do działającego kontenera (otwarcie nowej konsoli bash)
docker exec -it <ID_LUB_NAZWA_KONTENERA> bash

# Podgląd logów działającego kontenera
docker logs -f <ID_LUB_NAZWA_KONTENERA>

# Kopiowanie pliku z kontenera na swój komputer
docker cp <ID_KONTENERA>:/workspace/wyniki.csv ./wyniki.csv

# Kopiowanie pliku z komputera do kontenera
docker cp ./skrypt.py <ID_KONTENERA>:/workspace/skrypt.py

# Zwolnienie miejsca na dysku (usunięcie nieużywanych obrazów i warstw)
docker system prune -a
```
