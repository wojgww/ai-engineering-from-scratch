# Terminal & Shell — kurs praktyczny

Przejdziesz całą drogę od poruszania się po katalogach do uruchamiania treningu,
przetwarzania logów i kopiowania wyników. Kurs rozwija lekcję 10 z fazy 0.
[Ściąga wszystkich komend i aliasów](SCIAGA.md) pozostaje materiałem referencyjnym.

Do zadań 9–10 o przekierowaniu działającego procesu i sieci przejdź do
[kursu Linux: procesy, deskryptory i sieć](linux-network-course/README.md).

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

### Jak czytać polecenia

Ogólny zapis to `komenda [opcje] [argumenty]`. Nawiasy kwadratowe w opisach
znaczą „opcjonalne” — nie wpisujesz ich dosłownie. Opcje zmieniają zachowanie,
argumenty wskazują np. plik, wzorzec lub katalog. W `head -n 5 train.log`
komendą jest head, opcją -n, jej wartością 5, a argumentem plik train.log.
Krótkie opcje często można łączyć: `ls -la` to `ls -l -a`.
Opcje nie są wspólne dla wszystkich programów: `-n` znaczy co innego w head i sort.

Shell najpierw interpretuje zmienne, wzorce i przekierowania, potem uruchamia
program. `*.log` rozwija do nazw plików; `'*.log'` przekazuje dosłownie, co
przydaje się w find. `"$COURSE_PID"` rozwija zmienną i zachowuje ją jako jeden
argument. Pojedyncze cudzysłowy blokują rozwijanie zmiennych przez shell.
`--` w wielu programach kończy listę opcji, np. `grep -- '-1' plik.txt` szuka
tekstu -1, zamiast traktować go jako opcję.

Pomoc: `ls --help`, `man ls`, `help cd`. Man opisuje narzędzia systemowe,
help wbudowane polecenia Basha; w man klawisz q wychodzi, `/tekst` szuka.
Man może wymagać doinstalowania. Poniższe opcje dotyczą Basha i typowych
narzędzi Ubuntu; wersje macOS mogą się różnić.

## 1. Orientacja w katalogach · 10 minut

**Cel:** wiesz, względem którego katalogu shell szuka plików.
`pwd` pokazuje bieżący katalog, `ls -la` jego zawartość, `cd` zmienia katalog.
`.` oznacza tutaj, `..` poziom wyżej, `~` katalog domowy.

**Jak działają komendy i argumenty:**

| Komenda / składnia | Działanie i przydatne opcje |
|---|---|
| `pwd` | Wypisuje bieżącą ścieżkę. `-P` pokazuje fizyczną ścieżkę po rozwiązaniu dowiązań. |
| `ls [opcje] [ścieżka]` | Wyświetla nazwy w katalogu; domyślnie bieżącym. `-l` szczegóły, `-a` także ukryte, `-h` czytelne rozmiary z -l, `-t` najnowsze modyfikacje najpierw, `-r` odwrotna kolejność, `-d` sam katalog zamiast jego zawartości. |
| `cd [katalog]` | Zmienia katalog aktualnego shella. Bez argumentu wraca do domu; `cd -` wraca do poprzedniego katalogu. `cd ..` wchodzi poziom wyżej. |
| `echo [tekst...]` | Wypisuje argumenty zakończone nową linią. `-n` pomija tę linię. Do zwykłych notatek nie potrzebujesz opcji. |
| `mkdir -p ścieżka` | Tworzy brakujące katalogi po drodze; nie zgłasza błędu, jeśli już istnieją. |
| `clear` | Czyści widok terminala; historia poleceń pozostaje dostępna. |

Przykład: `ls -lh models` pokazuje szczegóły modeli z rozmiarami w czytelnych jednostkach.
W kolumnie rozmiaru katalogu ls nie podaje sumy rozmiarów wszystkich jego plików.

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

**Jak działają komendy i argumenty:**

| Komenda / składnia | Działanie i przydatne opcje |
|---|---|
| `cat [pliki...]` | Łączy treści wskazanych plików i wypisuje je na stdout. `-n` numeruje wszystkie wiersze. |
| `head -n N plik` | Pokazuje pierwsze N wierszy; bez opcji 10. Lekcyjne `head -3` to skrót `head -n 3`. |
| `tail -n N plik` | Pokazuje ostatnie N wierszy; bez opcji 10. `-f` czeka na dopisywane dane, `-F` także ponawia otwieranie po zastąpieniu pliku. |
| `grep [opcje] wzorzec [pliki...]` | Wypisuje pasujące wiersze, domyślnie przez wyrażenie regularne. `-i` ignoruje wielkość liter, `-n` dodaje numer wiersza, `-v` wybiera niepasujące, `-c` liczy pasujące wiersze osobno dla plików, `-F` szuka tekstu dosłownie, `-E` włącza rozszerzone wzorce, `-r` przeszukuje katalogi. |
| `wc [opcje] [pliki...]` | Zlicza dane. `-l` znaki nowej linii, `-w` słowa, `-c` bajty. W naszych logach każdy wiersz ma końcową nową linię. |
| `awk 'program' [plik]` | Przetwarza kolejne wiersze na pola: `$1` pierwsze, `$NF` ostatnie, `$0` cały wiersz. `-F '='` ustawia separator pól; domyślnie białe znaki. |
| `sort [opcje] [plik]` | Domyślnie sortuje tekstowo. `-n` liczbowo, `-r` malejąco, `-t '='` separator, `-k2,2` wyłącznie pole 2, `-u` usuwa powtórzone linie, `-h` rozumie rozmiary K/M/G. |
| `diff [opcje] plik1 plik2` | Porównuje wiersze. `-u` dodaje kontekst zmian, `-q` tylko informuje, czy pliki się różnią. Kod 0: identyczne, 1: różne, >1: problem wykonania. |

Przykłady: `grep -nF 'loss:' train.log` dodaje numery znalezionych wierszy;
`grep -E 'loss:|final_accuracy' train.log` wybiera jeden z dwóch wzorców.
Awk w tym kursie czyta logi; `awk -F,` nie jest pełnym parserem CSV z polami
zawierającymi przecinki w cudzysłowach.

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

**Jak działają komendy i argumenty:**

Program czyta stdin (deskryptor 0), wypisuje wynik na stdout (1), a komunikaty
na stderr (2). Potok przekazuje tylko stdout, dopóki nie połączysz strumieni.
Przekierowania interpretuje shell, a nie Python czy grep.

| Zapis / komenda | Działanie i przydatne opcje |
|---|---|
| `> plik`, `>> plik` | Zapis stdout: odpowiednio od nowa albo na końcu. Shell otwiera plik jeszcze przed uruchomieniem programu. |
| `2> plik`, `2>> plik` | Zapis lub dopisywanie stderr. |
| `> plik 2>&1` | Kieruje oba strumienie do pliku. Odwrotna kolejność nie daje tego samego wyniku: stderr zachowuje wcześniejszy cel stdout. |
| `tee [-a] plik` | Kopiuje stdin na ekran i do pliku. Domyślnie nadpisuje; `-a` dopisuje. |
| `python3 -u train.py [opcje skryptu]` | Interpreter uruchamia skrypt. `-u` wyłącza buforowanie stdout/stderr; opcje po nazwie train.py obsługuje już sam skrypt. |
| `--epochs N`, `--lr X`, `--delay S`, `--model ŚCIEŻKA` | Opcje naszego train.py: liczba epok, współczynnik uczenia, pauza między epokami, plik modelu. `--help` wyświetla ich opis. |
| `grep --line-buffered wzorzec` | Wysyła dopasowania wiersz po wierszu, zamiast czekać na zapełnienie bufora; przydatne za tail -f. |

Przykład: `python3 -u train.py --epochs 10 --delay 0.1 2>&1 | tee -a scratch/course/history.log`.
Nie używaj `grep ... train.log > train.log`: shell wyzeruje wejściowy plik,
zanim grep zdąży go przeczytać. Zapisuj wynik pod inną nazwą.

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

**Jak działają komendy i argumenty:**

| Komenda / zapis | Działanie i przydatne opcje |
|---|---|
| `komenda &` | Uruchamia asynchronicznie; shell od razu przyjmuje kolejne komendy. `$!` odczytuj zaraz po starcie właściwego zadania. |
| `jobs [-l]` | Zadania bieżącego shella; `-l` pokazuje również PID. Numery w nawiasach kwadratowych służą do zapisu `%1`, `%2` itd. |
| `fg %N`, `bg %N` | Wznawia zadanie N na pierwszym planie lub w tle. Ctrl+Z zawiesza zadanie na pierwszym planie; bg pozwala je wznowić bez zajmowania terminala. |
| `ps aux` | Migawka procesów: `a` rozszerza wybór procesów z terminalami, `u` format z użytkownikiem i zasobami, `x` uwzględnia procesy bez terminala. To składnia bez myślnika. |
| `ps -p PID -o pid,stat,etime,args` | Wybiera konkretny PID i kolumny: identyfikator, stan, czas działania, polecenie. |
| `pgrep [-af] wzorzec` | Szuka procesów. Domyślnie po nazwie; `-f` przeszukuje pełną linię komendy, `-a` wypisuje ją obok PID. |
| `kill [-TERM] PID` | Wysyła sygnał, domyślnie TERM. `-STOP` zawiesza, `-CONT` wznawia. `-KILL` wymusza zakończenie bez możliwości sprzątania przez program — w tych ćwiczeniach wystarczy TERM. |
| `nohup komenda` | Uruchamia komendę z ignorowaniem SIGHUP. Sam nie uruchamia w tle: dodaj &. Wskaż własny log zamiast polegać na domyślnym nohup.out. |
| `pkill -f wzorzec` | Wysyła sygnał do wszystkich procesów pasujących pełną linią komendy. W kursie tylko czytamy ten wariant; proces kończymy zapisanym PID. |

Przykład: `ps -p "$COURSE_PID" -o pid,stat,etime,args` pozwala sprawdzić dokładnie
Twój proces. Status T oznacza zatrzymanie, R działanie/gotowość, S oczekiwanie.

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

**Jak działają komendy i argumenty:**

Tmux ma sesje, w nich okna, a w oknach panele. Programy uruchamiają się w panelach;
zamknięcie widoku klienta nie usuwa automatycznie sesji na serwerze tmux.

| Komenda | Działanie i przydatne argumenty |
|---|---|
| `tmux new -s NAZWA` | Tworzy nazwaną sesję i dołącza do niej. `new` to skrót new-session; `-d` tworzy bez dołączania. |
| `tmux ls` | Lista sesji; skrót list-sessions. Brak serwera/sesji może dać niezerowy kod. |
| `tmux attach -t NAZWA` | Dołącza do sesji wybranej przez target -t. |
| `tmux split-window -h` | Dzieli panel na lewy i prawy; `-v` na górny i dolny. `-t NAZWA` pozwala wskazać cel. |
| `tmux new-window -n NAZWA` | Tworzy nowe okno w sesji; -n nadaje mu nazwę. Skrót klawiaturowy: Ctrl+B, potem c. |
| `tmux kill-session -t NAZWA` | Usuwa tylko wskazaną sesję; nie używaj kill-server do sprzątania pojedynczego ćwiczenia. |
| `tmux -V` | Pokazuje wersję programu. |

Prefix Ctrl+B naciśnij i puść przed drugim klawiszem. Ctrl+B, potem d odłącza
klienta. W sesji Ctrl+B, potem n wybiera następne okno, p poprzednie.
`sudo apt install tmux`: sudo uruchamia z uprawnieniami administratora,
apt install instaluje pakiet. Brew install to wariant z lekcji dla macOS.

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

**Jak działają komendy i argumenty:**

| Komenda / składnia | Działanie i przydatne opcje |
|---|---|
| `htop [-p PID]` | Interaktywny widok procesów i zasobów; -p ogranicza widok do wskazanego procesu. F9 wybiera sygnał, więc w tym kursie do zakończenia używaj znanego PID z działu 4. |
| `top -p PID` | Alternatywny interaktywny monitor jednego procesu; `-b -n 1` wypisuje pojedynczą migawkę bez interaktywnego widoku. |
| `nvtop` | Monitor wykorzystania GPU i procesów; widoczność sprzętu zależy od sterownika, uprawnień i środowiska. |
| `watch -n 1 komenda` | Powtarza komendę co sekundę; `-n 2` co dwie sekundy, `-d` wyróżnia zmiany. Ctrl+C kończy. |
| `nvidia-smi` | Odczytuje stan sterownika i kart NVIDIA. `-L` lista GPU, `-l 1` odświeżanie co sekundę, `--query-gpu=name,memory.used,memory.total --format=csv` wybrane pola tabeli. |
| `--query-compute-apps=pid,name,used_memory --format=csv` | Opcje nvidia-smi wybierające procesy obliczeniowe GPU i format wyniku; to inna tabela niż query-gpu. |
| `df -h [ścieżka]` | Wykorzystanie systemów plików. -h czytelne jednostki, -T typ systemu; ścieżka ogranicza wynik do jej systemu plików. |
| `du -sh ścieżka` | Zajętość plików/katalogów: -s jedna suma na argument, -h czytelne jednostki; `--max-depth=1` pokazuje też podkatalogi pierwszego poziomu. |
| `env` | Wypisuje eksportowane zmienne środowiska. `env NAZWA=wartość komenda` ustawia zmienną tylko dla uruchomionego programu. |
| `date [+FORMAT]` | Pokazuje czas; `date '+%Y-%m-%d %H:%M:%S'` wybiera format, -u czas UTC. |

Przykład: `watch -n 2 -d nvidia-smi` odświeża GPU co dwie sekundy i zaznacza
zmiany. Odczyt dotyczy maszyny/środowiska, w którym wykonałeś komendę.

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

**Jak działają komendy i argumenty:**

| Komenda / składnia | Działanie i przydatne opcje |
|---|---|
| `find katalog warunki` | Przechodzi po katalogach. `-type f` tylko zwykłe pliki, `-name '*.json'` nazwa z wzorcem, `-size +100M` pliki większe od 100 MiB. `-o` to lub; grupy zapisuj jako `\(` i `\)`, aby shell przekazał nawiasy. |
| `find ... -print0` | Oddziela nazwy bajtem NUL zamiast nową linią, dzięki czemu spacje w nazwach nie dzielą argumentów. |
| `xargs -0 -r komenda` | Czyta argumenty zakończone NUL i uruchamia komendę; -r w GNU xargs nie uruchamia jej przy pustej liście. Bez -0 zwykłe białe znaki i cudzysłowy wpływają na podział. |
| `tar -xzf archiwum -C katalog` | -x rozpakuj, -z gzip, -f nazwa pliku archiwum, -C katalog docelowy (musi istnieć). `tar -tzf archiwum` wyświetla zawartość bez rozpakowania; -v dopisuje listę obsługiwanych plików. |
| `wget [-O plik] URL` | Pobiera URL; -O wybiera ścieżkę wyniku i ją nadpisuje. `-c` próbuje wznowić pobieranie, `--spider` sprawdza zasób bez pobierania jego treści. |
| `rsync -avz źródło cel` | -a tryb archiwizacji (rekurencja i zachowanie m.in. czasów/uprawnień), -v szczegóły, -z kompresja przesyłanych danych. `-n` symulacja bez zapisu, `--progress` postęp, -c porównanie sum kontrolnych zamiast domyślnego rozmiaru/czasu. |
| `python3 -m http.server PORT` | -m uruchamia moduł Pythona. `--bind 127.0.0.1` nasłuchuje tylko lokalnie, `--directory data` wybiera udostępniony katalog. |

Przykład: `rsync -avnc data/ scratch/course/copy/` sprawdza plan synchronizacji
z porównaniem treści. Zwykłe rsync nie usuwa nadmiarowych plików celu.
W kursie nie potrzebujesz opcji --delete. Kompresja -z daje sens głównie przy
transferze przez sieć, nie przy kopiowaniu między katalogami tego samego dysku.

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

## 8. SSH i transfer plików na własny serwer · 30–45 minut

**Cel:** łączysz się z własnym serwerem, wysyłasz rzeczywisty CSV z labu,
odbierasz jego kopię i synchronizujesz katalog. Na końcu możesz przećwiczyć tunel.
Wszystkie polecenia, poza wyraźnie opisanymi, wpisujesz **lokalnie w katalogu labu**.
Nie potrzebujesz sudo ani zmian w usługach serwera. Użyj konta, którym już się logujesz.

### 8.1. Przygotuj połączenie

Potrzebujesz adresu serwera, loginu, portu SSH i działającej metody logowania.
Skorzystaj ze swojego istniejącego klucza lub hasła; nie generuj nowego klucza,
jeśli masz już działający dostęp. Rsync musi być zainstalowany po obu stronach.

Utwórz `scratch/course/ssh-config`, zastępując adres i login swoimi wartościami.
Jeśli port jest inny niż 22, zmień także Port. Plik jest lokalny i ignorowany przez Git.
Nie wpisuj do niego hasła ani treści klucza prywatnego.

```text
Host kurs-server
    HostName ADRES_TWOJEGO_SERWERA
    User TWOJ_LOGIN
    Port 22
    # Jeśli korzystasz z konkretnego klucza, odkomentuj i popraw ścieżkę:
    # IdentityFile ~/.ssh/twoj_klucz
```

`kurs-server` to lokalny alias — nie nazwa, którą musisz ustawiać na serwerze.
Opcja `-F` wybiera ten plik zamiast standardowego ~/.ssh/config. Dlatego przenieś
też potrzebne ustawienia działającego połączenia, np. klucz, ProxyJump lub inny port.
Klucz z domyślnej ścieżki lub ssh-agent może zostać znaleziony automatycznie.
Przy pierwszym połączeniu sprawdź odcisk klucza hosta na podstawie panelu dostawcy
lub zaufanej informacji o swoim serwerze. Nie wyłączaj jego weryfikacji.

**Jak działają komendy i argumenty:**

| Komenda / składnia | Działanie i przydatne opcje |
|---|---|
| `ssh -F PLIK ALIAS [komenda]` | Łączy się według konfiguracji. Bez komendy otwiera zdalny shell; z komendą wykonuje ją zdalnie i kończy połączenie. |
| `ssh -i KLUCZ -p PORT USER@HOST` | Jawne wskazanie klucza i portu, jeśli nie korzystasz z aliasu. |
| `ssh -G -F PLIK ALIAS` | Pokazuje rozwiniętą konfigurację bez łączenia. Nie potwierdza działania klucza ani serwera. |
| `ssh -v ...` | Pokazuje diagnostykę połączenia; przydatne przy błędzie uwierzytelnienia. |
| `scp -F PLIK źródło cel` | Kopiuje plik. `ALIAS:ścieżka` oznacza stronę zdalną; bez dwukropka ścieżka jest lokalna. |
| `scp -P PORT -i KLUCZ ...` | Port podaje się dużym -P, inaczej niż w ssh. -r kopiuje katalogi. |
| `rsync -avzi -e 'ssh -F PLIK' źródło cel` | Synchronizuje przez wskazane SSH: -a zachowuje strukturę i metadane, -v opisuje pracę, -z kompresuje, -i wypisuje zmiany. -n dodaje symulację bez zapisu. |
| `ssh -N -L LOKALNY_ADRES:PORT:ZDALNY_ADRES:PORT ...` | Tworzy tunel; -N nie otwiera zdalnej powłoki. Opcja -o ExitOnForwardFailure=yes kończy SSH, jeśli nie uda się utworzyć przekierowania. |

**Zadania:**

1. Przygotuj plik konfiguracji i sprawdź hostname, user oraz port przez ssh -G.
2. Połącz się interaktywnie. W zdalnym shellu wykonaj `hostname`, `whoami`, `pwd`,
   a potem `exit`, aby wrócić do lokalnego terminala.
3. Sprawdź dostępność rsync lokalnie oraz zdalnie. Jeśli brakuje go na serwerze,
   zadania scp nadal są wykonalne; instalację rsync wykonaj oddzielnie świadomie.

**Sprawdzenie:** [ ] potrafisz rozpoznać lokalny i zdalny terminal oraz wrócić przez exit.

<details>
<summary>Rozwiązanie: konfiguracja i pierwsze połączenie</summary>

```bash
mkdir -p scratch/course
```

Zapisz powyższą konfigurację w edytorze jako scratch/course/ssh-config, a następnie:

```bash
chmod 600 scratch/course/ssh-config
ssh -G -F scratch/course/ssh-config kurs-server | grep -E '^(hostname|user|port|identityfile) '
ssh -F scratch/course/ssh-config kurs-server
```

Poniższe trzy komendy wykonaj **na serwerze**, następnie wróć przez exit:

```bash
hostname
whoami
pwd
exit
```

Znowu lokalnie:

```bash
command -v rsync
ssh -F scratch/course/ssh-config kurs-server 'command -v rsync'
```

`chmod 600` daje odczyt i zapis tylko właścicielowi pliku.
Pojedyncze cudzysłowy wokół komendy zdalnej chronią jej treść przed lokalnym shellem.

</details>

### 8.2. Wyślij CSV i pobierz go z powrotem

Pracuj dalej w **tym samym lokalnym terminalu**. Utworzysz osobny katalog
ćwiczenia w katalogu domowym konta na serwerze. Nazwa z datą oddziela kolejne próby.
Ścieżka po dwukropku jest względna do zdalnego katalogu domowego.

**Zadania:**

1. Ustaw REMOTE_DIR z datą i utwórz zdalnie podkatalogi incoming oraz synced.
2. Wyślij `data/lessons.csv` przez scp do incoming/lessons.csv.
3. Pobierz go pod lokalną nazwą scratch/course/from-server.csv.
4. Porównaj kopię przez diff; potwierdź zgodność także przez sha256sum.
5. Wyjaśnij, dlaczego zamiana źródła i celu odwraca kierunek transferu.

<details>
<summary>Rozwiązanie: scp w obie strony</summary>

```bash
REMOTE_DIR="shell-course/$(date +%Y%m%d-%H%M%S)"
echo "$REMOTE_DIR"
ssh -F scratch/course/ssh-config kurs-server "mkdir -p '$REMOTE_DIR/incoming' '$REMOTE_DIR/synced'"
scp -F scratch/course/ssh-config data/lessons.csv "kurs-server:$REMOTE_DIR/incoming/lessons.csv"
scp -F scratch/course/ssh-config "kurs-server:$REMOTE_DIR/incoming/lessons.csv" scratch/course/from-server.csv
diff data/lessons.csv scratch/course/from-server.csv
sha256sum data/lessons.csv scratch/course/from-server.csv
```

Diff bez wyniku oznacza identyczne pliki. Obie sumy SHA-256 powinny być takie same.
Jeśli otworzysz nowy terminal, odtwórz REMOTE_DIR z zapisanego wyniku echo — nie
ustawiaj nowej daty, jeśli chcesz kontynuować na tych samych zdalnych plikach.
Podwójne cudzysłowy pozwalają lokalnie rozwinąć kontrolowaną nazwę REMOTE_DIR.

</details>

### 8.3. Synchronizuj katalog zamiast pojedynczego pliku

**Zadania:**

1. Przygotuj własny katalog scratch/course/ssh-upload z kopiami lessons.csv i source.json.
2. Obejrzyj plan synchronizacji do zdalnego synced/ przez rsync -n.
3. Wykonaj synchronizację, a potem uruchom ją ponownie. Zobacz, czy pliki są ponownie przesyłane.
4. Dodaj lokalną notatkę w ssh-upload, ponów synchronizację i potwierdź jej treść na serwerze.
5. Wyjaśnij znaczenie końcowego / w ścieżce źródłowej.

<details>
<summary>Rozwiązanie: rsync i zmiana jednego pliku</summary>

```bash
mkdir -p scratch/course/ssh-upload
cp data/lessons.csv data/source.json scratch/course/ssh-upload/
rsync -avzin -e 'ssh -F scratch/course/ssh-config' scratch/course/ssh-upload/ "kurs-server:$REMOTE_DIR/synced/"
rsync -avzi -e 'ssh -F scratch/course/ssh-config' scratch/course/ssh-upload/ "kurs-server:$REMOTE_DIR/synced/"
rsync -avzi -e 'ssh -F scratch/course/ssh-config' scratch/course/ssh-upload/ "kurs-server:$REMOTE_DIR/synced/"
echo 'Notatka z kursu SSH' > scratch/course/ssh-upload/notatka.txt
rsync -avzi -e 'ssh -F scratch/course/ssh-config' scratch/course/ssh-upload/ "kurs-server:$REMOTE_DIR/synced/"
ssh -F scratch/course/ssh-config kurs-server "cat '$REMOTE_DIR/synced/notatka.txt'"
```

Pierwsza komenda rsync to tylko symulacja. Drugie rzeczywiste uruchomienie
bez zmiany plików zwykle nie przesyła ich ponownie. Rsync domyślnie sprawdza
rozmiary/czasy, a -i opisuje wykryte zmiany. Źródłowe ssh-upload/ oznacza jego
zawartość. Nie potrzebujesz --delete; nie usuwaj innych katalogów serwera.

</details>

### 8.4. Opcjonalnie: tunel SSH do własnej usługi

**Cel:** pobrać dane z serwera HTTP, który nasłuchuje wyłącznie na loopback
serwera, bez otwierania jego portu HTTP w firewallu. Wymagane Python 3 na serwerze
oraz dozwolone przekierowania TCP w konfiguracji SSH. Nie zmieniaj jej w ramach zadania.

**Zadania:**

1. W lokalnym terminalu A (z ustawionym REMOTE_DIR) uruchom przez SSH testowy
   HTTP na zdalnym 127.0.0.1:18765, udostępniający wyłącznie katalog synced.
2. W lokalnym B utwórz tunel 127.0.0.1:18766 → zdalne 127.0.0.1:18765.
3. W lokalnym C pobierz przez curl lessons.csv i porównaj z oryginałem.
4. Zakończ tunel w B i własny serwer testowy w A przez Ctrl+C. Nie kończ sesji
   przed zatrzymaniem programu HTTP; ssh -t zapewnia mu zdalny terminal.

<details>
<summary>Rozwiązanie: trzy terminale</summary>

Terminal A, w katalogu labu, z REMOTE_DIR z działu 8.2:

```bash
ssh -F scratch/course/ssh-config kurs-server 'command -v python3'
ssh -t -F scratch/course/ssh-config kurs-server "python3 -m http.server 18765 --bind 127.0.0.1 --directory '$REMOTE_DIR/synced'"
```

Terminal B, również w katalogu labu:

```bash
ssh -F scratch/course/ssh-config -N -o ExitOnForwardFailure=yes -L 127.0.0.1:18766:127.0.0.1:18765 kurs-server
```

Terminal C, w katalogu labu:

```bash
curl --noproxy '*' --fail --max-time 10 http://127.0.0.1:18766/lessons.csv -o scratch/course/from-tunnel.csv
diff data/lessons.csv scratch/course/from-tunnel.csv
```

Pierwsze 127.0.0.1 w -L to lokalny adres nasłuchu; drugie odnosi się do serwera.
Tunel działa tylko, dopóki działa sesja B; serwer HTTP tylko, dopóki działa A.
ExitOnForwardFailure wykrywa błąd utworzenia nasłuchu, ale nie potwierdza,
że zdalny HTTP działa — to sprawdza dopiero curl. Jeśli port jest zajęty,
wybierz inny i zmień odpowiedni numer we wszystkich komendach; nie kończ obcej usługi.

</details>

**Zaliczenie działu 8:** [ ] działające SSH i rozróżnienie lokalne/zdalne;
[ ] zgodny CSV po wysłaniu i pobraniu; [ ] rzeczywista synchronizacja katalogu
oraz nowej notatki. [ ] Opcjonalnie poprawny tunel i zakończony testowy serwer.
Zapisz wyniki w scratch/course/progress.md, bez haseł i kluczy.
Przygotowanie instrukcji nie oznacza wykonania połączeń ani zmian na Twoim serwerze.

## 9. Aliasy i funkcje · 15 minut

**Cel:** tworzysz własne skróty. Alias zastępuje nazwę komendą, funkcja może
obsłużyć argumenty. Source wykonuje plik w aktualnym shellu, zachowując definicje.

**Jak działają komendy i argumenty:**

| Komenda / zapis | Działanie i przydatne argumenty |
|---|---|
| `alias nazwa='komenda'` | Definiuje rozwinięcie nazwy w interaktywnym shellu. `alias nazwa` pokazuje definicję, samo alias listę definicji. Alias nie ma własnych parametrów $1/$2 jak funkcja. |
| `unalias nazwa` | Usuwa konkretny alias z bieżącego shella. Nie zmienia pliku, z którego został wczytany. |
| `source plik [argumenty...]` | Wykonuje plik w aktualnym shellu; skrót to `. plik`. Używaj do plików, których zawartość znasz, bo to normalne wykonanie kodu. |
| `nazwa() { komendy; }` | Definiuje funkcję; $1 to pierwszy argument, $2 drugi, `"$@"` wszystkie argumenty z zachowaniem ich granic. `${1:-5}` wybiera 5 przy braku/pustym argumencie. |
| `type nazwa`, `command -v nazwa` | Pierwsze opisuje rodzaj/definicję polecenia; drugie pokazuje sposób jego odnalezienia i zwraca błąd, jeśli go brak. Przydatne do sprawdzenia, czy działa alias czy program. |

Przykład: `type clast` pokazuje treść funkcji, a `alias closs` definicję skrótu.
`source aliases.sh` zachowuje definicje w tym terminalu; `bash aliases.sh` wykonuje
plik w osobnym procesie, więc po jego zakończeniu nowe aliasy nie zostają w rodzicu.
Pomocnicze funkcje z lekcji (np. newexp) są kodem shella, a nie osobnymi pakietami.

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

**Jak działają konstrukcje i argumenty:**

| Zapis / komenda | Działanie i przydatne warianty |
|---|---|
| `for x in a b c; do ...; done` | Przypisuje kolejno każdą wartość do x i wykonuje ciało pętli. `"$x"` przekazuje bieżącą wartość jako jeden argument. |
| `seq KONIEC` / `seq START KROK KONIEC` | Generuje liczby; `seq 1 2 5` daje 1, 3, 5. `seq 1 3` to zakres z domyślnym krokiem 1. |
| `sleep CZAS` | Pauzuje; na Ubuntu 0.1 oznacza 0.1 sekundy, 2m dwie minuty. |
| `echo 'scale=4; 1/3' \| bc` | Bc czyta obliczenie ze stdin; scale ustala liczbę cyfr dziesiętnych dzielenia. `bc -l` ładuje bibliotekę matematyczną i ustawia domyślnie scale=20. |
| `$(komenda)` | Wstawia stdout komendy, usuwając końcowe nowe linie. Nie jest uruchomieniem w tle. W ogólnym przypadku ujmij rozwinięcie w podwójne cudzysłowy. |
| `a; b`, `a && b`, `a \| b` | Po średniku b wykona się zawsze; po && tylko przy kodzie 0 komendy a; po potoku b przetwarza stdout komendy a. |
| `set -o pipefail` / `set +o pipefail` | Włącza/wyłącza uwzględnianie błędów wcześniejszych elementów potoku. Gdy kilka komend zawiedzie, kod pochodzi od ostatniej nieudanej komendy w kolejności potoku. |
| `$?`, `--help` | $? to kod ostatniego polecenia/potoku (0 zwykle sukces); --help to częsta, ale nie uniwersalna opcja pomocy programu. Nie jest osobną komendą. |
| `mail -s 'temat' ADRES` | -s ustawia temat; treść mail czyta ze stdin. Wymaga klienta i transportu poczty; w tym kursie niczego nie wysyłamy. |

Przykład: `python3 train.py --epochs 5 --delay 0 && echo 'Sukces'` wypisze
potwierdzenie tylko po poprawnym zakończeniu treningu. Zwykła pętla for sama nie
przerywa przy pierwszym błędzie — w mini-projekcie sprawdź każdy log osobno.

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
