# VS Code + Docker — Python bez lokalnego uv sync

## Dlaczego VS Code podkreśla import datasets?

Biblioteka może być zainstalowana w Dockerze, podczas gdy lokalne okno VS Code
analizuje kod przy użyciu Pythona z komputera. Samo otwarcie terminala kontenera
nie zmienia środowiska, z którego korzysta edytor i Pylance.

Rozwiązanie: otworzyć okno VS Code połączone z kontenerem i wybrać jego interpreter.
Nie trzeba instalować tych samych bibliotek lokalnie przez uv sync.

## 1. Uruchom środowisko

W terminalu komputera:

```bash
cd /home/ai_workspace/Projekty/ai-engineering-from-scratch/with_nvidia_gpu
docker compose up -d
docker compose ps
```

## 2. Połącz VS Code z kontenerem

1. Zainstaluj rozszerzenie **Dev Containers**, jeśli go nie masz.
2. Naciśnij **Ctrl+Shift+P**.
3. Wybierz **Dev Containers: Attach to Running Container...**.
4. Wskaż `with_nvidia_gpu-ai-dev-1` lub aktualną nazwę usługi `ai-dev` z compose ps.
5. W nowym oknie VS Code wybierz **File → Open Folder** i otwórz `/workspace`.
6. Otwórz swój plik Python w tym nowym oknie.

Zakres plików widocznych pod /workspace zależy od montowania w docker-compose.yml.
Sprawdź, czy otwierasz plik udostępniony z komputera, żeby zachować swoje zmiany.

## 3. Wybierz Python z kontenera

1. W rozszerzeniach zainstaluj **Python** i **Pylance w kontenerze**, jeżeli są
   dostępne tylko lokalnie. VS Code może pokazać przycisk Install in Container.
2. Naciśnij **Ctrl+Shift+P** i wybierz **Python: Select Interpreter**.
3. Wybierz **Enter interpreter path** i podaj:

```text
/opt/venv/bin/python
```

Ta ścieżka dotyczy naszego profilu Docker; wybieraj ją w oknie połączonym
z kontenerem, nie w zwykłym lokalnym oknie VS Code.

## 4. Sprawdź środowisko

W terminalu nowego okna VS Code:

```bash
python -c "import sys; print(sys.executable)"
python -c "import datasets; print(datasets.__version__)"
```

Oczekiwana ścieżka interpretera: `/opt/venv/bin/python`.
Druga komenda powinna wypisać wersję datasets bez błędu importu.
Jeśli import działa, a podkreślenie pozostaje, wykonaj **Developer: Reload Window**
i ponownie sprawdź wybrany interpreter oraz instalację Pylance w kontenerze.

Jeżeli import nie działa także w kontenerze, sprawdź jego zależności i używany
obraz — sama zmiana ustawień edytora nie instaluje brakujących pakietów.

## Codzienna praca

- Edytuj kod w oknie VS Code połączonym z kontenerem.
- Terminal, uruchamianie plików Python i debugowanie korzystają wtedy z kontenera
  oraz wybranego interpretera. Zewnętrzne rozszerzenia uruchamiające kod mogą
  wymagać własnej konfiguracji.
- Nową zależność dodawaj na komputerze w katalogu profilu:

```bash
uv add --no-sync nazwa-pakietu
docker compose up -d --build
```

- Po odtworzeniu kontenera może być potrzebne ponowne połączenie VS Code.
- Nie wykonuj lokalnego uv sync, jeśli nie zamierzasz uruchamiać kodu na hoście.
- Nie wyłączaj ostrzeżeń o importach tylko po to, żeby ukryć problem z interpreterem.

Instrukcja przygotowana 2026-11-04. Samo zapisanie notatki nie zmienia ustawień
VS Code ani nie instaluje rozszerzeń.
