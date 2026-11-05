# Terminal & Shell — kurs praktyczny

Przejdziesz całą drogę od poruszania się po katalogach do uruchamiania treningu,
przetwarzania logów i kopiowania wyników. Kurs rozwija lekcję 10 z fazy 0.
[Ściąga wszystkich komend i aliasów](SCIAGA.md) pozostaje materiałem referencyjnym.

Pracuj w Bash na Ubuntu, po jednym dziale. Najpierw wykonaj przykład,
potem samodzielnie zadania. Rozwiązania pod każdym działem są schowane.
Odhaczaj zaliczenie dopiero po wykonaniu. Orientacyjnie 2–3 godziny łącznie;
możesz rozłożyć je na kilka sesji. Przydadzą się dwa okna terminala.

## Przygotowanie

```bash
cd /home/ai_workspace/Projekty/ai-engineering-from-scratch/terminal-shell-lab
pwd
ls -la
mkdir -p scratch/course
```

Dane już istnieją: `data/lessons.csv` opisuje 448 rzeczywistych lekcji,
`train.log` zawiera 80 epok treningu, `results/*.log` trzy eksperymenty,
`models/*.json` ich wagi, a `dataset.tar.gz` archiwum danych.
Jeśli tych plików brakuje, uruchom `python3 prepare.py`. Nie uruchamiaj go
między zadaniami — odtwarza i nadpisuje bazowe wyniki.

`train.py` to mały trening CPU bez dodatkowych bibliotek. Nie musisz jeszcze
rozumieć jego algorytmu: uczysz się obsługi programu z terminala.
Swoje rezultaty zapisuj w `scratch/course/`. W nowym terminalu zawsze najpierw
wejdź do katalogu labu. Polecenia wykonuj pojedynczo, nie cały dokument naraz.

## 1. Orientacja w katalogach · 10 minut

**Cel:** wiesz, względem którego katalogu shell szuka plików.
`pwd` pokazuje bieżący katalog, `ls -la` jego zawartość, `cd` zmienia katalog.
`.` oznacza tutaj, `..` poziom wyżej, `~` katalog domowy.

```bash
cd data
pwd
ls -la
cd ..
```

**Zadania:**

1. Wypisz `$SHELL` i `$0`. Pierwsze opisuje domyślną powłokę konta;
   drugie pomaga rozpoznać bieżącą powłokę interaktywną.
2. Wejdź do `models` ścieżką względną, pokaż pliki i wróć do labu.
3. Wejdź do katalogu domowego, następnie wróć do labu ścieżką absolutną.
4. Znajdź wcześniejsze `pwd` przez Ctrl+R i wyczyść ekran Ctrl+L lub `clear`.

**Zaliczenie:** [ ] końcowe pwd wskazuje lab; umiesz wyjaśnić ścieżkę względną
i absolutną. Czyszczenie widoku nie usuwa plików.

<details>
<summary>Rozwiązanie</summary>

```bash
echo "$SHELL"
echo "$0"
cd models
ls -la
cd ..
cd ~
cd /home/ai_workspace/Projekty/ai-engineering-from-scratch/terminal-shell-lab
pwd
```

</details>

## 2. Czytanie i filtrowanie · 15 minut

**Cel:** znajdujesz potrzebne informacje bez otwierania całego pliku w edytorze.
`cat` czyta całość, `head` początek, `tail` koniec, `grep` wybiera wiersze,
`wc -l` je liczy, `awk` wybiera pola, `sort` porządkuje wynik.

```bash
head -3 data/lessons.csv
grep 'final_accuracy' results/*.log
```

**Zadania:**

1. Przeczytaj `data/source.json`. Co oznacza etykieta `is_build`?
2. Pokaż ostatnie trzy wiersze `train.log`.
3. Policz wiersze zawierające `loss:`; pokaż osobno same wartości loss.
4. Posortuj eksperymenty malejąco po final_accuracy. Który wygrał?
5. Porównaj przez diff wiersze accuracy z eksperymentów short i medium.

**Zaliczenie:** [ ] 80 wierszy loss; short ma najwyższą testową accuracy
w przygotowanym zestawie. Więcej epok nie musi poprawiać tego wyniku.
Diff zwraca 1 przy różnicach, a 0 przy identycznych danych.

<details>
<summary>Rozwiązanie</summary>

```bash
cat data/source.json
tail -3 train.log
grep 'loss:' train.log | wc -l
grep 'loss:' train.log | awk '{print $NF}'
grep 'final_accuracy' results/*.log | sort -t= -k2 -n -r
diff <(grep 'accuracy' results/short.log) <(grep 'accuracy' results/medium.log)
```

Etykieta 1 oznacza deklarowany typ Build, 0 pozostałe typy.
`$NF` to ostatnie pole wiersza. Sort: separator =, drugie pole, liczbowo, malejąco.

</details>

## 3. Potoki, przekierowania i logi na żywo · 20 minut

**Cel:** rozdzielasz wynik od komunikatów i zapisujesz oba.
`|` łączy stdout z wejściem następnej komendy. `>` nadpisuje, `>>` dopisuje,
`2>` zapisuje stderr, `2>&1` kieruje stderr tam, gdzie aktualnie idzie stdout.

```bash
python3 train.py --epochs 3 --delay 0 > scratch/course/example.log 2> scratch/course/example.err
cat scratch/course/example.err
```

**Zadania:**

1. Zapisz wartości loss z train.log do `scratch/course/losses.txt`.
2. Dopisz dwie notatki do `scratch/course/notes.txt` przez echo i >>.
3. Uruchom 5 epok, stdout zapisz do `scratch/course/run.log`, stderr do `run.err`
   w tym samym katalogu. Sprawdź oba pliki.
4. Uruchom 5 epok, połącz strumienie, wyświetl je i zapisz równocześnie przez tee.
5. Wywołaj trening z `--lr -1`, zapisz stderr i od razu sprawdź `echo "$?"`.
6. W terminalu A uruchom 100 epok z opóźnieniem 0.3 s do `logs/live.log`.
   W B śledź tylko loss przez tail -f i grep --line-buffered. Zakończ podgląd Ctrl+C.

**Zaliczenie:** [ ] 80 wartości w pliku; run.log zawiera 5 epok; run.err ma INFO;
niepoprawny lr daje kod 2; widzisz przyrastający log. Stderr nie zawsze oznacza błąd.
Tail -f sam nie kończy się po treningu. `$?` opisuje ostatnią wykonaną komendę.

<details>
<summary>Rozwiązanie</summary>

```bash
grep 'loss:' train.log | awk '{print $NF}' > scratch/course/losses.txt
wc -l scratch/course/losses.txt
echo 'Pierwszy trening' >> scratch/course/notes.txt
echo 'Sprawdzilem logi' >> scratch/course/notes.txt
python3 train.py --epochs 5 --delay 0 > scratch/course/run.log 2> scratch/course/run.err
cat scratch/course/run.log
cat scratch/course/run.err
python3 train.py --epochs 5 --delay 0 2>&1 | tee scratch/course/combined.log
python3 train.py --lr -1 2> scratch/course/invalid.err
echo "$?"
```

Terminal A:

```bash
python3 -u train.py --epochs 100 --delay 0.3 > logs/live.log 2>&1
```

Terminal B, w katalogu labu:

```bash
tail -f logs/live.log | grep --line-buffered 'loss:'
```

</details>

## 4. Procesy i praca w tle · 15 minut

**Cel:** rozpoznajesz własny proces, wznawiasz go i kończysz.
`&` uruchamia w tle, `$!` zawiera PID tego zadania, `jobs` pokazuje zadania
bieżącej powłoki, `ps` procesy, `pgrep` szuka procesów, `fg` przywraca zadanie.

```bash
python3 -u train.py --epochs 300 --delay 0.3 > scratch/course/background.log 2>&1 &
COURSE_PID=$!
jobs
```

**Zadania:**

1. Znajdź trening przez ps aux z grep oraz pgrep -af.
2. Odczytaj numer zadania z jobs. Wykonaj `fg %NUMER`, potem Ctrl+Z.
   Zobacz stan Stopped przez jobs, wznowienie przez fg, a na końcu przerwij Ctrl+C.
3. Uruchom nowy trening przez nohup, zapisz jego PID i odczytaj koniec logu.
4. Zakończ tylko ten proces przez kill ze wskazanym PID. Sprawdź jobs.

**Zaliczenie:** [ ] odróżniasz numer zadania od PID; potrafisz wznowić zawieszony
proces; nie zostawiłeś treningów z tego działu w tle. Nie używaj masowego pkill.

<details>
<summary>Rozwiązanie</summary>

```bash
ps aux | grep '[t]rain.py'
pgrep -af 'python3.*train.py'
jobs
```

Numer do fg weź z jobs. `%1` jest poprawne tylko, jeśli zadanie ma numer 1.
Po przećwiczeniu fg / Ctrl+Z / fg / Ctrl+C:

```bash
nohup python3 -u train.py --epochs 300 --delay 0.3 > scratch/course/nohup.log 2>&1 &
COURSE_PID=$!
ps -p "$COURSE_PID"
tail scratch/course/nohup.log
kill "$COURSE_PID"
jobs
```

Poczekaj chwilę na pierwszy wiersz logu. Nohup ignoruje SIGHUP po zamknięciu
terminala, ale nie chroni przed restartem komputera. Samo & nie gwarantuje przetrwania.

</details>

## 5. tmux — trzy panele · 15 minut

**Cel:** odłączasz terminal bez kończenia sesji.
Sprawdź `tmux -V`. Jeśli brakuje programu, zainstaluj na Ubuntu przez
`sudo apt install tmux` lub wróć do działu później. Nic nie instalowano za Ciebie.

```bash
tmux new -s course-shell
```

**Zadania:**

1. W pierwszym panelu uruchom trening 300 epok, delay 0.3, do logs/tmux.log.
2. Ctrl+B, potem `"`: podziel panel; w nowym uruchom `watch -n1 date`.
3. Ctrl+B, potem `%`: stwórz trzeci panel; uruchom `tail -f logs/tmux.log`.
4. Przechodź między panelami przez Ctrl+B i strzałki. Odłącz: Ctrl+B, potem d.
5. Pokaż listę sesji, dołącz ponownie, sprawdź czy log przyrósł.
6. Odłącz i zakończ wyłącznie sesję course-shell.

**Zaliczenie:** [ ] trzy panele; trening postępował po odłączeniu; zawartość paneli
zachowała się po powrocie. Ten dział wymaga faktycznego użycia tmux.

<details>
<summary>Rozwiązanie</summary>

Panel treningu, w katalogu labu:

```bash
python3 -u train.py --epochs 300 --delay 0.3 > logs/tmux.log 2>&1
```

Po odłączeniu:

```bash
tmux ls
tmux attach -t course-shell
```

Po ponownym odłączeniu:

```bash
tmux kill-session -t course-shell
```

Zakończenie sesji zamyka jej panele i może zakończyć działające tam programy.

</details>

## 6. Monitoring CPU, RAM, GPU i dysku · 15 minut

**Cel:** odczytujesz stan komputera. Htop pokazuje procesy i CPU/RAM,
nvidia-smi stan GPU NVIDIA, df miejsce w systemie plików, du rozmiary plików.

```bash
df -h .
du -sh data models
```

**Zadania:**

1. W htop znajdź trening (uruchom go jak w dziale 4). Wyszukaj przez /,
   posortuj przez F6 i obejrzyj drzewo przez F5. Wyjdź q. Jeśli brak htop, użyj top.
2. Odczytaj wolne miejsce na partycji labu i rozmiar danych. Zapisz te wartości
   własnymi słowami do scratch/course/monitoring.txt przez echo i >>.
3. Na hoście NVIDIA odczytaj nvidia-smi, potem watch -n1 nvidia-smi;
   zakończ Ctrl+C. Pokaż osobno tabelę procesów obliczeniowych GPU.
4. Sprawdź zmienne CUDA i Torch przez env z grep -i. Co oznacza brak trafień?
5. Opcjonalnie, jeśli masz nvtop, porównaj jego widok z nvidia-smi.

**Zaliczenie:** [ ] masz notatkę z odczytanymi wartościami i wyjaśniasz różnicę
df/du. Nasz trening używa CPU, więc brak procesu GPU jest normalny.
Jeśli GPU jest niedostępne, zapisz ograniczenie i wykonaj część CPU/dysk.
Zakończ uruchomiony trening, jeśli nadal działa.

<details>
<summary>Rozwiązanie</summary>

```bash
htop
df -h .
du -sh data models
nvidia-smi
watch -n1 nvidia-smi
```

Po Ctrl+C:

```bash
nvidia-smi --query-compute-apps=pid,name,used_memory --format=csv
env | grep -i cuda
env | grep -i torch
```

Brak zmiennych nie dowodzi braku CUDA/PyTorch. Grep bez dopasowań zwraca 1.

</details>

## 7. Pliki, archiwa i pobieranie · 20 minut

**Cel:** znajdujesz artefakty, rozpakowujesz dane i sprawdzasz ich kopię.
Find szuka, xargs przekazuje nazwy kolejnej komendzie, tar rozpakowuje,
wget pobiera po HTTP, rsync synchronizuje katalogi.

```bash
find models -type f -name '*.json' -print0 | xargs -0 du -h
```

**Zadania:**

1. Policz linie w plikach .py labu przez find, xargs i wc.
2. Pokaż do 20 modeli posortowanych malejąco według rozmiaru.
3. Rozpakuj archiwum do scratch/course/unpacked; porównaj CSV z oryginałem.
4. Zsynchronizuj zawartość data/ do scratch/course/copy/; porównaj CSV.
5. W terminalu A udostępnij data lokalnie przez HTTP. W B pobierz CSV do
   scratch/course/download.csv przez wget i porównaj. Zatrzymaj serwer Ctrl+C.

**Zaliczenie:** [ ] trzy kopie CSV są identyczne z oryginałem.
Para -print0 / -0 obsługuje nazwy ze spacjami. Slash w data/ oznacza jego zawartość.

<details>
<summary>Rozwiązanie</summary>

```bash
find . -name '*.py' -print0 | xargs -0 wc -l | tail -1
find models -type f -name '*.json' -print0 | xargs -0 du -h | sort -rh | head -20
mkdir -p scratch/course/unpacked scratch/course/copy
tar xzf dataset.tar.gz -C scratch/course/unpacked
diff data/lessons.csv scratch/course/unpacked/lessons.csv
rsync -avz data/ scratch/course/copy/
diff data/lessons.csv scratch/course/copy/lessons.csv
```

Terminal A:

```bash
python3 -m http.server 8765 --bind 127.0.0.1 --directory data
```

Terminal B, w katalogu labu:

```bash
wget -O scratch/course/download.csv http://127.0.0.1:8765/lessons.csv
diff data/lessons.csv scratch/course/download.csv
```

Diff bez wyjścia oznacza identyczne pliki. Jeśli port jest zajęty, zmień go
w obu komendach. Du -h zaokrągla, więc przy małych modelach możliwe są remisy.

</details>

## 8. SSH, klucze i transfer · 15 minut

**Cel:** rozumiesz, gdzie wykonuje się komenda i w którą stronę kopiujesz.
Zdalna praktyka wymaga Twojego serwera i dostępu SSH. Bez niego wykonaj wariant
lokalny i oznacz transfer jako nieprzećwiczony. Localhost też wymaga serwera SSH.

**Zadania bez serwera:**

1. Utwórz scratch/course/ssh-config.example z Host gpu, HostName 192.0.2.10,
   User ubuntu i IdentityFile ~/.ssh/my_gpu_key. To adres dokumentacyjny.
2. Przez `ssh -G -F scratch/course/ssh-config.example gpu` odczytaj rozwiniętą
   konfigurację. -G wypisuje ją bez nawiązywania połączenia.
3. Zapisz w notatce kierunek obu scp z rozwiązania i znaczenie tunelu.

**Zadania z własnym serwerem:** odczytaj pwd przez SSH. Prześlij CSV do
istniejącego katalogu ćwiczeń, pobierz pod nową nazwą i porównaj przez diff.
Wypróbuj rsync. Tunel testuj tylko, jeśli masz zdalną usługę na porcie 8888.
Zastąp USER/HOST i ścieżki swoimi danymi; nie uruchamiaj szablonów dosłownie.

**Zaliczenie:** [ ] odczytujesz host/użytkownika/klucz z konfiguracji;
[ ] opcjonalnie zweryfikowałeś transfer. Sam ssh -G nie testuje połączenia ani klucza.

<details>
<summary>Rozwiązanie</summary>

```bash
cat > scratch/course/ssh-config.example <<'EOF'
Host gpu
    HostName 192.0.2.10
    User ubuntu
    IdentityFile ~/.ssh/my_gpu_key
EOF
ssh -G -F scratch/course/ssh-config.example gpu | grep -E '^(hostname|user|identityfile) '
```

`<<'EOF'` przekazuje kolejne linie jako wejście komendy aż do samodzielnego EOF.
Szablony dla własnego serwera:

```bash
ssh -i ~/.ssh/my_gpu_key USER@HOST
scp data/lessons.csv USER@HOST:~/shell-course/lessons.csv
scp USER@HOST:~/shell-course/lessons.csv scratch/course/from-server.csv
rsync -avz data/ USER@HOST:~/shell-course/
ssh -L 8888:localhost:8888 USER@HOST
```

Pierwsze scp wysyła, drugie pobiera. Tunel przekazuje lokalny port 8888 do portu
8888 widzianego jako localhost po stronie serwera. Zdalny katalog musi istnieć.

</details>

## 9. Aliasy i funkcje · 15 minut

**Cel:** tworzysz własne skróty. Alias zastępuje nazwę komendą, funkcja może
obsłużyć argumenty. Source wykonuje plik w aktualnym shellu, zachowując definicje.

```bash
alias coursepwd='pwd'
coursepwd
```

**Zadania:**

1. Utwórz scratch/course/aliases.sh: alias closs liczący wiersze loss w train.log
   i funkcję clast pokazującą wskazaną liczbę ostatnich wierszy (domyślnie 5).
2. Wczytaj plik przez source. Sprawdź closs i clast 3 z katalogu labu.
3. Wczytaj aliasy oryginalnej lekcji; wykonaj diskuse, memhogs, newexp shell-course
   i lastexp. Obejrzyj utworzony katalog eksperymentu.
4. Przeczytaj definicje killtraining, killtrain, hfdownload i trainenv.
   Zapisz, co robią; nie uruchamiaj ich w tym zadaniu.
5. Otwórz nowy terminal i sprawdź, czy własne aliasy są dostępne bez source.

**Zaliczenie:** [ ] closs zwraca 80; clast 3 pokazuje trzy wiersze;
wyjaśniasz, dlaczego definicje nie pojawiają się automatycznie w nowej powłoce.
Nie trzeba edytować .bashrc. Pełne aliasy opisuje [ściąga](SCIAGA.md).

<details>
<summary>Rozwiązanie</summary>

```bash
cat > scratch/course/aliases.sh <<'EOF'
alias closs="grep 'loss:' train.log | wc -l"
clast() {
    tail -n "${1:-5}" train.log
}
EOF
source scratch/course/aliases.sh
closs
clast 3
source ../phases/00-setup-and-tooling/10-terminal-and-shell/code/shell_aliases.sh
diskuse
memhogs
newexp shell-course
lastexp
```

Killtraining/killtrain kończą procesy według szerokiego wzorca, hfdownload pobiera
plik lub klonuje repo, trainenv tworzy tmux z monitoringiem. Newexp tworzy
lokalny katalog w experiments/. Własne skróty zakładają pracę z katalogu labu.

</details>

## 10. Pętle i mini-projekt końcowy · 20 minut

**Cel:** łączysz komendy w powtarzalny eksperyment. For powtarza polecenia,
seq generuje liczby, sleep robi przerwę, `$(...)` wstawia wynik komendy.
Średnik wykonuje kolejny krok niezależnie od sukcesu, && tylko po sukcesie.
Pipefail pozwala wykryć błąd komendy wewnątrz potoku.

```bash
for n in $(seq 1 3); do echo "Przebieg $n"; sleep 0.1; done
echo 'scale=4; 1/3' | bc
```

**Zadania:**

1. Pętlą uruchom treningi 5, 10 i 20 epok, delay 0. Każdy zapisuje własny log
   i model w scratch/course/. Posortuj końcowe accuracy malejąco.
2. Wyciągnij loss dla 20 epok do osobnego pliku. Sprawdź liczbę wierszy.
3. Przepuść błędny trening --lr -1 przez tee, raz bez pipefail, raz z pipefail.
   Po każdym odczytaj `$?`. Najpierw przewidź wyniki.
4. Utwórz scratch/course/summary.txt: trzy wyniki i własne wyjaśnienie,
   dlaczego echo DONE po średniku nie potwierdza sukcesu treningu.
5. Opcjonalnie sprawdź `command -v mail`. Wyjaśnij wymagania dla
   `mail -s 'Training complete' ADRES`. Wysyłanie poczty nie jest zadaniem kursu.

**Zaliczenie:** [ ] trzy logi i modele, 20 wartości loss, podsumowanie;
bez pipefail kod potoku to 0, z pipefail to 2. Brak bc pozwala pominąć sam kalkulator.

<details>
<summary>Rozwiązanie</summary>

```bash
for epochs in 5 10 20; do
    python3 train.py --epochs "$epochs" --delay 0 --model "scratch/course/model-$epochs.json" > "scratch/course/experiment-$epochs.log" 2>&1
done
grep 'final_accuracy' scratch/course/experiment-*.log | sort -t= -k2 -n -r
grep 'loss:' scratch/course/experiment-20.log | awk '{print $NF}' > scratch/course/final-losses.txt
wc -l scratch/course/final-losses.txt
set +o pipefail
python3 train.py --lr -1 2>&1 | tee scratch/course/failed.log
echo "$?"
set -o pipefail
python3 train.py --lr -1 2>&1 | tee scratch/course/failed.log
echo "$?"
grep 'final_accuracy' scratch/course/experiment-*.log | sort -t= -k2 -n -r > scratch/course/summary.txt
echo 'Srednik nie sprawdza sukcesu poprzedniej komendy.' >> scratch/course/summary.txt
```

Pipefail pozostaje włączone w tym Bash. Bez niego kod pochodzi od ostatniej
komendy potoku (tee), która zapisała plik poprawnie. Mail wymaga klienta
i skonfigurowanego transportu poczty.

</details>

## Twój postęp

Utwórz scratch/course/progress.md: zapisuj numery wykonanych działów, trudności
i części niewykonane z braku tmux/GPU/serwera. Nie wpisuj kluczy ani haseł.
Samo przeczytanie rozwiązania nie zalicza zadania. Ten kurs nie zmienia
automatycznie Twojego statusu ukończenia lekcji.
