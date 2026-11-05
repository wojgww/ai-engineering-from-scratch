# Terminal & Shell — ćwiczenia po polsku

To katalog do samodzielnej nauki lekcji `phases/00-setup-and-tooling/10-terminal-and-shell/docs/en.md`.
Polecenia poniżej wykonuj pojedynczo w Bash na Ubuntu. Na hoście masz dostęp do GPU;
w kontenerze zestaw narzędzi może być inny. `python3` zastępuje lekcyjne `python`.

## Start i prawdziwe dane

```bash
cd /home/ai_workspace/Projekty/ai-engineering-from-scratch/terminal-shell-lab
python3 prepare.py
```

Przygotowanie już wykonano. Ponowne uruchomienie nadpisuje pliki wejściowe i trzy
przykładowe wyniki treningu, więc najpierw zachowaj własne zmiany, jeśli je robiłeś.

- `data/lessons.csv`: prawdziwe tytuły, typy, ścieżki i policzone cechy dokumentów kursu.
- `data/source.json`: pochodzenie, liczba rekordów, definicje cech, SHA-256 CSV.
- `train.py`: rzeczywista regresja logistyczna przewidująca typ Build na podstawie
  liczby słów, bloków kodu i nagłówków. Podział 80/20, seed 42, normalizacja tylko na treningu.
- `train.log`, `logs/experiment.log`, `results/*.log`: wyniki rzeczywistych uruchomień.
- `models/*.json`: rzeczywiste wyuczone wagi, nie pliki udające modele PyTorch.
- `dataset.tar.gz`: archiwum CSV i opisu źródła; `scratch/`: miejsce na własne wyniki.

To małe ćwiczenie CPU. Nie obciąża GPU; `nvidia-smi` może pokazywać brak procesów.
Accuracy oznacza odsetek poprawnych przewidywań na części testowej. Ten zbiór służy
do nauki shella, nie do oceny przydatności klasyfikatora. Nigdy nie trenowaliśmy
tu dużego modelu. Nie dopisano wymyślonych błędów do logów.

## 1. Orientacja i skróty

Terminal to okno; shell, np. Bash, interpretuje wpisane polecenia.

| Komenda / skrót | Znaczenie |
|---|---|
| `echo "$SHELL"` | Wypisuje domyślną powłokę konta; nie musi być aktualnie uruchomioną. |
| `echo "$0"` | W interaktywnym terminalu pomaga rozpoznać bieżącą powłokę. |
| `pwd` | Wypisuje bieżący katalog. |
| `ls -la` | Lista plików: `-l` szczegóły, `-a` także ukryte. |
| `cd data`, `cd ..`, `cd ~` | Wejdź do katalogu, poziom wyżej, do katalogu domowego. |
| `clear` / Ctrl+L | Czyści widok terminala, nie pliki. |
| Ctrl+R | Szuka w historii; kolejne Ctrl+R przechodzi do wcześniejszych trafień. |
| Ctrl+C | Przerywa polecenie na pierwszym planie. |
| Ctrl+Z, potem `fg` | Zawiesza proces, potem wznawia go na pierwszym planie. |

Ścieżka względna zależy od `pwd`. `~` oznacza katalog domowy. Nazwy ze spacjami
otaczaj cudzysłowami. Gwiazdka `*.log` rozwija się do pasujących nazw plików.

## 2. Czytanie i filtrowanie

```bash
cat data/source.json
head -5 data/lessons.csv
tail -5 train.log
cat train.log | grep "loss" | wc -l
grep "loss:" train.log | awk '{print $NF}' > scratch/losses.txt
grep "final_accuracy" results/*.log | sort -t= -k2 -n -r
diff <(grep "accuracy" results/short.log) <(grep "accuracy" results/medium.log)
```

`cat` wypisuje plik, `head` początek, `tail` koniec. `grep` wybiera pasujące
wiersze, `wc -l` liczy wiersze, `awk '{print $NF}'` wypisuje ostatnie pole.
`sort`: separator `=`, druga kolumna, liczbowo i malejąco. `diff` pokazuje różnice;
kod wyjścia 1 oznacza znalezione różnice. `<(...)` przekazuje wynik komendy jak plik.
`grep` liczy tutaj wiersze z loss, nie każde wystąpienie tego słowa.

## 3. Potoki i przekierowania

Proces ma stdin (wejście), stdout (wynik, 1) i stderr (komunikaty, 2).

| Zapis | Działanie |
|---|---|
| `a \| b` | stdout komendy a staje się stdin komendy b. |
| `> plik` | Zapisuje stdout; nadpisuje istniejącą treść. |
| `>> plik` | Dopisuje stdout na końcu. |
| `2> plik` | Zapisuje stderr osobno. |
| `> plik 2>&1` | Najpierw kieruje stdout do pliku, potem stderr tam samo. Kolejność ma znaczenie. |
| `tee plik` | Pokazuje wynik i równocześnie zapisuje go do pliku. |
| `;` | Uruchamia następną komendę niezależnie od sukcesu poprzedniej. |
| `&&` | Uruchamia następną komendę tylko po sukcesie poprzedniej. |

```bash
python3 train.py --epochs 10 --delay 0 > scratch/output.log 2> scratch/errors.log
cat scratch/errors.log
python3 train.py --epochs 10 --delay 0 > scratch/full.log 2>&1
python3 train.py --epochs 10 --delay 0 2>&1 | tee scratch/tee.log
echo "moja notatka" >> scratch/notes.txt
```

W `errors.log` będzie INFO o podziale danych — stderr nie zawsze oznacza błąd.
Prawdziwy błąd walidacji uzyskasz przez `python3 train.py --lr -1` (exit 2).
Przy potokach `set -o pipefail` pozwala wykryć błąd treningu nawet jeśli `tee` się uda.

Podgląd na żywo: w pierwszym terminalu uruchom poniższy trening, w drugim `tail`.
`-u` wyłącza buforowanie Pythona; `--line-buffered` wyłącza opóźnianie wierszy grep.

```bash
python3 -u train.py --epochs 100 --delay 0.3 > logs/live.log 2>&1
```

```bash
tail -f logs/live.log | grep --line-buffered "loss"
```

`tail -f` czeka dalej po zakończeniu treningu; zakończ go Ctrl+C. W lekcyjnym
filtrze `grep --line-buffered "ERROR"` brak wyjścia jest normalny, jeśli brak błędów.

## 4. Procesy w tle

Wykonuj w jednym interaktywnym terminalu. Jeśli masz inne zadania, numer może być inny niż `%1`.

```bash
python3 -u train.py --epochs 300 --delay 0.3 > logs/background.log 2>&1 &
LAB_PID=$!
jobs
ps aux | grep '[t]rain.py'
pgrep -af 'python3.*train.py'
```

`&` oddaje terminal; `$!` zawiera PID ostatniego zadania w tle. `jobs` pokazuje
zadania tej powłoki, `ps aux` wszystkie widoczne procesy, `pgrep` wyszukuje ich PID-y.
`fg %1` przenosi zadanie 1 na pierwszy plan. `kill %1` lub `kill "$LAB_PID"`
wysyła domyślnie SIGTERM do konkretnego zadania/procesu.

```bash
kill "$LAB_PID"
nohup python3 -u train.py --epochs 100 --delay 0.3 > logs/nohup.log 2>&1 &
LAB_PID=$!
```

`nohup` ignoruje SIGHUP po zamknięciu terminala. Nie chroni przed restartem
komputera ani usunięciem kontenera. Samo `&` nie gwarantuje przetrwania zamknięcia.
`kill $(pgrep -f "train.py")` z lekcji oraz `pkill -f` mogą trafić wiele procesów;
na ćwiczeniu korzystaj z zapisanego PID. `$(...)` wstawia wynik komendy jako tekst.

## 5. tmux — kilka paneli i odłączanie

Na tym hoście nie znaleziono `tmux` w PATH podczas przygotowania. Instalacja z lekcji:
`sudo apt install tmux`; `brew install tmux` to odpowiednik dla macOS.

```bash
tmux new -s shell-lab
```

W pierwszym panelu uruchom trening z sekcji 3. Ctrl+B, a następnie `"` dzieli
panel na górę i dół; Ctrl+B, następnie `%` dzieli na lewo i prawo.
Ctrl+B, następnie strzałka wybiera panel. W pozostałych uruchom:

```bash
watch -n1 date
htop
```

Ctrl+B, potem `d` odłącza; procesy działają dalej. Po odłączeniu:

```bash
tmux ls
tmux attach -t shell-lab
```

`tmux kill-session -t shell-lab` kończy tę sesję wraz z jej panelami.
`screen` to alternatywny multiplekser wspomniany w porównaniu w lekcji.

## 6. Monitoring komputera

```bash
htop
nvidia-smi
watch -n1 nvidia-smi
nvidia-smi --query-compute-apps=pid,name,used_memory --format=csv
df -h
du -sh data/*
env | grep -i cuda
env | grep -i torch
```

`htop`: CPU, RAM, procesy; F6 sortuje, F5 pokazuje drzewo, `/` szuka,
F9 wysyła sygnał do wybranego procesu, q wychodzi. `top` to prostsza alternatywa.
`nvtop` pokazuje interaktywnie GPU (nie znaleziono go tutaj; w lekcji instalacja
`sudo apt install nvtop`, na macOS `brew install nvtop`).
`nvidia-smi` podaje stan NVIDIA; `watch -n1` powtarza komendę co sekundę; Ctrl+C kończy.
`date` wypisuje czas. `df` mierzy miejsce w systemach plików, `du` rozmiar plików.
`env` wypisuje zmienne środowiska; `grep -i` ignoruje wielkość liter.
Brak zmiennych CUDA/Torch nie oznacza, że biblioteki nie działają.

## 7. Pliki, archiwa i pobieranie

```bash
mkdir -p scratch/unpacked
tar xzf dataset.tar.gz -C scratch/unpacked
find . -name "*.py" -print0 | xargs -0 wc -l | tail -1
find models -type f -name '*.json' -print0 | xargs -0 du -h | sort -rh | head -20
rsync -avz data/ remote-copy/
```

`mkdir -p` tworzy katalogi także po drodze. `tar xzf`: rozpakuj (x), gzip (z),
plik (f); `-C` wybiera katalog docelowy. `find` szuka, `xargs` przekazuje
znalezione nazwy do polecenia. Para `-print0` / `-0` obsługuje spacje w nazwach.
`sort -rh` sortuje malejąco rozmiary z K/M/G; `head -20` bierze pierwszych 20.
Wzorzec modeli z lekcji to `find . \( -name '*.pt' -o -name '*.safetensors' \)`;
tu używamy `.json`, bo właśnie takie prawdziwe modele zapisuje trening.
`rsync -avz`: zachowuje strukturę/metadane (a), wypisuje postęp (v), kompresuje
transfer (z). Końcowy `/` w `data/` oznacza zawartość tego katalogu.

`wget URL` pobiera plik. Lekcyjne `https://huggingface.co/model/...` jest
szablonem, nie adresem konkretnego modelu. Do ćwiczenia bez zewnętrznych pobrań
udostępnij lokalnie CSV w terminalu A, potem pobierz go w terminalu B:

```bash
python3 -m http.server 8765 --bind 127.0.0.1 --directory data
```

```bash
wget -O scratch/lessons-downloaded.csv http://127.0.0.1:8765/lessons.csv
diff data/lessons.csv scratch/lessons-downloaded.csv
```

Brak wyjścia `diff` oznacza identyczne pliki. Serwer zakończ Ctrl+C.

## 8. SSH, scp i zdalny rsync

Te przykłady to szablony — wymagają Twojego serwera, konta i klucza. Nie zostały
uruchomione. `localhost` też wymaga działającego serwera SSH; sam klient nie wystarczy.

```bash
ssh USER@HOST
ssh -i ~/.ssh/my_gpu_key USER@HOST
scp models/latest.json USER@HOST:~/models/
scp USER@HOST:~/results/metrics.json scratch/
rsync -avz data/ USER@HOST:~/data/
ssh -L 8888:localhost:8888 USER@HOST
```

`ssh` otwiera zdalną powłokę; `-i` wskazuje klucz. `scp` kopiuje pliki;
dwukropek oddziela host od ścieżki. `rsync` synchronizuje katalogi.
`ssh -L` udostępnia lokalny port 8888 do usługi na porcie 8888 widzianej z serwera.
Katalogi docelowe i usługa muszą istnieć. Skrót do hosta w `~/.ssh/config`:

```text
Host gpu
    HostName ADRES_TWOJEGO_SERWERA
    User TWOJ_LOGIN
    IdentityFile ~/.ssh/my_gpu_key
```

Wtedy `ssh gpu` korzysta z tego wpisu. Klucz prywatny pozostaje na Twoim komputerze.

## 9. Aliasy i funkcje z pliku lekcji

`alias nazwa='komenda'` definiuje skrót; `source plik` wykonuje plik w bieżącym
shellu, więc aliasy i funkcje zostają w tej sesji. Nie trzeba od razu edytować `.bashrc`.

```bash
source ../phases/00-setup-and-tooling/10-terminal-and-shell/code/shell_aliases.sh
```

| Nazwy | Co uruchamiają / wymagają |
|---|---|
| `gpu`, `gpuwatch`, `gpumem`, `gpuprocs` | Stan GPU, odświeżanie, pamięć, procesy przez nvidia-smi. |
| `killtraining`, `killtrain [wzorzec]` | `pkill -f`: kończą wszystkie pasujące procesy, nie tylko ćwiczenie. |
| `ae`, `de` | Aktywują `.venv` / wywołują `deactivate` po aktywacji środowiska. |
| `mkvenv`, `uvvenv` | Tworzą `.venv` przez `python -m venv` / `uv venv` i aktywują ją. |
| `watchloss`, `watchacc`, `watcherr` | Śledzą pasujące wiersze z `logs/*.log`. Ctrl+C kończy. |
| `taillog [wzorzec]` | Jak wyżej, domyślnie szuka loss. |
| `diskuse`, `bigfiles`, `bigmodels` | Wolne miejsce, pliki >100 MB, modele o rozszerzeniach z lekcji. |
| `checkgpu`, `checkcuda`, `checkenv` | Test PyTorch/CUDA, zmienne CUDA, wersje Python/pip/PyTorch. Wymagają właściwego środowiska. |
| `ta NAZWA`, `tls`, `tn NAZWA`, `tk NAZWA` | tmux: dołącz, lista, nowa sesja, zakończ sesję. |
| `trainenv [nazwa]` | Tworzy tmux z trzema panelami, monitoringiem GPU i htop. |
| `syncto host ścieżka [lokalny]` | rsync z lokalnego katalogu do hosta, domyślnie z `.`. |
| `syncfrom host ścieżka [lokalny]` | rsync z hosta do lokalnego katalogu, domyślnie do `.`. |
| `newexp [nazwa]`, `lastexp` | Tworzy katalog eksperymentu z datą / pokazuje ostatnio zmieniony katalog eksperymentu. |
| `hfdownload model [plik]` | wget pojedynczego pliku; bez nazwy pliku: `git lfs install`, `git clone`. |
| `memhogs`, `psg wzorzec` | Procesy według RAM / procesy pasujące do wzorca. |

`pip --version`, `python --version`, `uv venv`, `git clone`, `git lfs install`
to odpowiednio wersja instalatora, wersja Pythona, tworzenie środowiska,
klonowanie repo i konfiguracja obsługi dużych plików Git. Sam lab ich nie wymaga.
Funkcje pliku lekcji używają `python`, więc np. `checkenv` może wymagać aktywacji venv.
Aliasy `bigfiles`/`bigmodels` używają prostego xargs; do nazw ze spacjami wybierz
wariant `-print0` / `-0` z sekcji 7. `lastexp` bazuje na czasie modyfikacji.

## 10. Pozostałe składniki przykładów z lekcji

- `for ...; do ...; done` to pętla; `seq 1 100` wypisuje liczby 1–100.
- `sleep 0.1` robi przerwę; `bc` oblicza wyrażenia, `scale=4` ustala precyzję
  dzielenia. Lekcyjna pętla generuje sztuczny loss `1/i`; tutaj mamy prawdziwy trening.
- `mail -s "temat" adres` wysyła e-mail, wymaga skonfigurowanej poczty.
  Nie znaleziono `mail` na tym hoście. `echo DONE` jedynie wypisuje tekst;
  po `;` pojawi się nawet po nieudanym treningu. Po `&&` tylko po sukcesie.
- `source ~/.bashrc` / `source ~/.zshrc` ponownie wykonuje konfigurację shella;
  dopisanie source aliasów do tego pliku czyni je dostępnymi w kolejnych terminalach.

## Twoja kolej — 5 zadań

1. Wypisz ostatnie 3 wiersze `train.log` i policz wiersze zawierające loss.
2. Zapisz same wartości loss do `scratch/moje-losses.txt`.
3. Znajdź eksperyment z najwyższym final_accuracy. Remisy są możliwe.
4. Uruchom trening na 100 epok w tle, znajdź go przez `jobs`, zakończ jego PID.
5. Rozpakuj archiwum do nowego katalogu i porównaj CSV z oryginałem.

Kontrola pierwszych zadań: przygotowany `train.log` ma 80 wierszy loss,
a plik wyciągniętych wartości powinien mieć 80 wierszy i po jednej liczbie w wierszu.
To przygotowanie ćwiczeń nie oznacza jeszcze zaliczenia lekcji.
