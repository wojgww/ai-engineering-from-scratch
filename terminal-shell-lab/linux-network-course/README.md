# Linux: procesy, deskryptory i sieć — kurs do zadań 9 i 10

Ten kurs prowadzi od podstaw do wszystkich punktów z przesłanego zrzutu.
Każdy dział ma wyjaśnienie, argumenty komend, zadania i rozwijane rozwiązanie.
Pracuj w Bash na Ubuntu, po jednym dziale; całość to około 3–5 godzin.
Potrzebujesz dwóch, czasami trzech okien terminala na tej samej maszynie.

**Prostsza strona do ćwiczeń:** Twoje `http://127.0.0.1:8080/` — mały serwer
dołączony do kursu, bez HTTPS, reklam i przekierowań. Dla zadań z publiczną
domeną wybieramy **`http://neverssl.com/`** zamiast example.com.
Sprawdzono jego odpowiedź HTTP 200 podczas przygotowania, 2026-11-06 czasu polskiego.
Publiczna strona może później odpowiadać inaczej; lokalny serwer daje stały przebieg.

| Część zrzutu | Działy kursu |
|---|---|
| 9: zmiana wejścia/wyjścia już działającego procesu | 1–3 |
| 10.1: handshake TCP i stany ss | 4–5 |
| 10.2: ręczne HTTP, nc i curl | 6 |
| 10.3: DNS i dig +trace | 7 |
| 10.4: strace i kroki żądania | 8 |
| 10.5: porty, PID, /proc i bind | 9 |
| Konwersja man do PDF | 10 |
| Materiał do własnego raportu | 11 |

## 0. Przygotuj środowisko i pliki

W każdym nowym terminalu wejdź tutaj:

```bash
cd /home/ai_workspace/Projekty/ai-engineering-from-scratch/terminal-shell-lab/linux-network-course
mkdir -p scratch
```

Pliki: `io_demo.py` wypisuje prawdziwe komunikaty z PID i numerem kroku;
`stdin.txt` zawiera tekst do wejścia procesu; `server.py` udostępnia prostą
stronę `web/index.html`, `/health` i odpowiedzi 404. Wszystko działa na stdlib Pythona.
Program I/O kończy się domyślnie po 300 krokach, serwer po 900 sekundach.
Nie wymagają uruchamiania Docker ani innych usług.

**Sprawdź dostępność narzędzi:**

```bash
for cmd in python3 gdb ip ss dig nc tcpdump strace curl man ps2pdf groff; do
    command -v "$cmd" || echo "Brakuje: $cmd"
done
```

Jeżeli brakuje pakietów, na Ubuntu polecenie instalacji wygląda tak
(instalacja jest krokiem do samodzielnego wykonania, nie częścią uruchomienia skryptów):

```bash
sudo apt update
sudo apt install python3 gdb iproute2 dnsutils netcat-openbsd tcpdump strace curl man-db manpages groff ghostscript
```

`sudo` wykonuje polecenie z uprawnieniami administratora. `command -v` sprawdza,
jak shell znajduje komendę. Opcje `nc` poniżej dotyczą **OpenBSD netcat** z Ubuntu.
Pracuj na hoście/VM: kontener i sandbox mogą blokować ptrace, netlink i przechwytywanie
pakietów mimo obecności programu. Nie zmieniaj globalnych zabezpieczeń systemu.
Wszystkie własne wyniki zapisuj w ignorowanym `scratch/`.

**Zadanie:** sprawdź narzędzia i zapisz w scratch/notatki.md środowisko oraz braki.
**Zaliczenie:** [ ] wiesz, gdzie wykonujesz komendy i które narzędzia są dostępne.

## 1. Proces i jego deskryptory: stdin, stdout, stderr

**Cel:** rozumiesz `/proc/PID/fd`. Proces ma tabelę otwartych deskryptorów:
0 zwykle stdin, 1 stdout, 2 stderr. Numer jest lokalny dla procesu: fd 1
Twojego shella i fd 1 Pythona mogą wskazywać różne obiekty.

`/proc` to widok informacji jądra, nie zwykły katalog na dysku.
Link `/proc/PID/fd/1` pokazuje cel stdout procesu PID: terminal `/dev/pts/...`,
plik, potok `pipe:[...]` albo gniazdo `socket:[...]`.

| Komenda | Jak działa i przydatne argumenty |
|---|---|
| `sleep 1000 &` | Uruchamia pauzę w tle; proces istnieje, choć nic nie wypisuje. |
| `PID=$!` | Zapamiętuje PID ostatniego zadania uruchomionego w tle w tym shellu. |
| `ls -l /proc/PID/fd` | Długi format pokazuje cele dowiązań deskryptorów. |
| `readlink /proc/PID/fd/1` | Wypisuje sam cel wskazanego dowiązania. |
| `ps -p PID -o pid,etime,args` | Wybiera proces i kolumny: PID, czas życia, polecenie. |

W jednym terminalu:

```bash
python3 -u io_demo.py --ticks 300 --interval 1 &
IO_PID=$!
ls -l "/proc/$IO_PID/fd"
readlink "/proc/$IO_PID/fd/1"
ps -p "$IO_PID" -o pid,etime,args
```

`--ticks` to liczba kroków, `--interval` pauza między nimi. Program używa
`os.write`, więc wynik nie czeka w buforze Pythona. W tle stdin może wskazywać
terminal, ale jego czytanie podlega regułom kontroli zadań; tutaj nie włączamy czytania.

**Zadania:**

1. Odczytaj cele fd 0, 1 i 2. Zapisz je wraz z PID.
2. Uruchom drugi proces, od początku przekierowany do dwóch plików.
   Porównaj jego fd 1 i 2 z pierwszym procesem.
3. Zakończ wyłącznie te dwa własne procesy po wykonaniu obserwacji.

**Zaliczenie:** [ ] umiesz wskazać, gdzie idą stdout i stderr każdego procesu.
To dział wprowadzający; zadanie 9 wymaga zmiany po starcie, czego tutaj jeszcze nie robimy.

<details>
<summary>Rozwiązanie</summary>

```bash
python3 -u io_demo.py --ticks 300 > scratch/start-out.log 2> scratch/start-err.log &
SECOND_PID=$!
ls -l "/proc/$SECOND_PID/fd"
kill "$IO_PID" "$SECOND_PID"
```

Procesy mogły już skończyć, jeśli minęło 300 sekund. Nie zastępuj PID wzorcem
`pkill python`, bo dotyczyłby też innych programów.

</details>

## 2. Zmień stdout działającego procesu przez GDB

**Cel:** wykonać istotę zadania 9: ten sam PID, a nowy cel fd 1.
Samo `echo tekst > /proc/PID/fd/1` zapisze tekst do aktualnego celu — **nie zmieni
tabeli deskryptorów tego procesu**. Potrzebujesz operacji wewnątrz procesu.

GDB pozwala zatrzymać proces i wywołać w nim funkcje libc:

1. `open` otwiera plik w procesie i zwraca nowy deskryptor.
2. `dup2(nowy, 1)` sprawia, że fd 1 wskazuje ten sam otwarty plik.
3. `close(nowy)` zamyka dodatkowy numer; fd 1 pozostaje otwarty.

Nie restartujesz procesu ani nie kończysz go podczas zmiany. Debugger **na chwilę
zatrzymuje jego wykonanie**, a następnie je wznawia. To nie operacja bez pauzy.

| Komenda GDB | Działanie |
|---|---|
| `run` | Uruchamia program pod kontrolą debuggera. |
| `catch syscall NAZWY...` | Zatrzymuje przy wejściu do wskazanego wywołania systemowego i przy powrocie z niego. |
| `disable 1` | Wyłącza punkt zatrzymania o numerze 1, aby program nie stawał na każdej następnej pauzie. |
| Ctrl+C | W terminalu GDB zatrzymuje debugowany program do inspekcji. |
| `info inferiors` | Pokazuje debugowane procesy i ich PID. |
| `set $nazwa = ...` | Zapisuje wartość w zmiennej GDB; to nie zmienna Basha. |
| `call (int)funkcja(...)` | Wywołuje funkcję wewnątrz debugowanego procesu; rzutowanie podaje typ wyniku, gdy brak symboli debugowania libc. |
| `continue` | Wznawia proces pod kontrolą GDB. |
| `detach` | Odłącza debugger i pozwala procesowi działać dalej samodzielnie. |
| `quit` | Kończy GDB. Po detach nie kończy odłączonego procesu. |

### Wariant podstawowy: GDB uruchamia proces

Na Ubuntu z Yama `ptrace_scope=1` zwykłe dołączenie innego procesu do uruchomionego
w shellu programu może być zabronione. GDB jako rodzic swojego procesu zwykle
nie ma tego ograniczenia — dlatego uczymy się najpierw tego wariantu.

Terminal A:

```bash
gdb -q --args python3 -u io_demo.py --ticks 600 --interval 1
```

Wpisuj poniższe **w GDB**, nie w Bash. Zatrzymamy program na końcu pierwszej
pauzy. To bardziej powtarzalne miejsce do wykonywania funkcji niż wejście
do wywołania systemowego. Na tym Ubuntu pauza Pythona używa pselect6,
a w nowszych wersjach może korzystać z clock_nanosleep.

```text
catch syscall pselect6 clock_nanosleep
run
```

Gdy zobaczysz `call to syscall ...`, wpisz `continue`. Gdy pojawi się
`returned from syscall ...`, wyłącz catchpoint. W nowej sesji jest to numer 1;
jeśli dodałeś inne punkty zatrzymania, numer odczytaj z komunikatu GDB.

```text
continue
disable 1
```

Teraz wykonaj zmianę:

```text
info inferiors
set $saved_stdout = (int)dup(1)
print $saved_stdout
set $out = (int)open("scratch/stdout-live.log", 1089, 0600)
print $out
```

Oba deskryptory muszą być nieujemne. Przy -1 przerwij tę sekwencję i sprawdź
ścieżkę/uprawnienia; nie wywołuj dup2 z niepoprawnym deskryptorem.
`1089` to Linuxowe `O_WRONLY | O_CREAT | O_APPEND` (1 + 64 + 1024),
`0600` to ósemkowe uprawnienia: odczyt i zapis dla właściciela nowego pliku.
Istniejący plik zachowuje uprawnienia. Append dopisuje; nie kasuje starej zawartości.

```text
call (int)dup2($out, 1)
call (int)close($out)
continue
```

Dup2 ma zwrócić 1, close 0. Terminal A pokazuje teraz tylko stderr.
Terminal B: podstaw PID wyświetlony przez info inferiors; nie kopiuj przykładowej liczby:

```bash
TARGET_PID=WPISZ_PID_Z_GDB
ls -l "/proc/$TARGET_PID/fd"
tail -f scratch/stdout-live.log
```

Po obserwacji Ctrl+C w terminalu B kończy tylko tail. W A Ctrl+C zatrzymuje
program w GDB. Możesz przywrócić stdout:

```text
call (int)dup2($saved_stdout, 1)
call (int)close($saved_stdout)
detach
quit
```

Program jest nadal tym samym procesem i działa po odłączeniu; zakończ go dopiero
po zebraniu dowodów przez `kill "$TARGET_PID"` w B.

**Zadania:** zapisz PID, cele fd przed/po oraz fragment dopisywanego pliku.
Wyjaśnij kolejno open, dup2, close i różnicę między pauzą a restartem.
**Zaliczenie:** [ ] PID nie zmienił się; fd 1 wskazuje plik; numery tick dalej rosną.

<details>
<summary>Wariant dokładnie jak na zrzucie: attach do sleep</summary>

```bash
sleep 1000 &
SLEEP_PID=$!
ls -l "/proc/$SLEEP_PID/fd"
gdb -q -p "$SLEEP_PID"
```

Jeśli ptrace_scope odrzuci dołączenie do Twojego własnego sleep, możesz użyć
`sudo gdb -q -p "$SLEEP_PID"` na swoim hoście (wymaga administratora),
albo ćwiczyć wariant z GDB jako rodzicem. Nie wyłączaj Yama przez sysctl.
Ograniczenia kontenera/seccomp lub tryb Yama 3 mogą blokować także administratora.

W GDB wykonaj otwarcie pliku/dup2/close jak wyżej, potem detach i quit.
Sprawdź ponownie /proc. Sleep nie wypisuje danych, więc sam plik może pozostać
pusty — dowodem jest cel fd 1 i niezmieniony PID. Kill dopiero kończy ćwiczenie.

Przy błędach wywołań funkcji w GDB (np. zapis rejestrów, ptrace) zapisz pełny
komunikat: nie deklaruj zmiany deskryptora, jeśli dup2 się nie udało.

</details>

## 3. Przekieruj także stderr i stdin po starcie

**Cel:** uogólnić zmianę fd 1 na fd 2 i 0. To ćwiczenie dotyczy wyłącznie
naszego jednowątkowego programu, który świadomie odczytuje deskryptor 0.
Nie zakładaj takiego samego zachowania buforowanych strumieni dowolnej aplikacji.

Terminal A: uruchom nowy proces przez GDB:

```bash
gdb -q --args python3 -u io_demo.py --read-input --ticks 600 --interval 1
```

W nowej sesji GDB powtórz `catch syscall pselect6 clock_nanosleep`, `run`,
`continue` do komunikatu returned from syscall, następnie `disable 1`, jak
w dziale 2. Teraz:

```text
set $err = (int)open("scratch/stderr-live.log", 1089, 0600)
print $err
```

Jeśli wynik >= 0:

```text
call (int)dup2($err, 2)
call (int)close($err)
set $in = (int)open("stdin.txt", 0)
print $in
```

Drugi argument open równy 0 to `O_RDONLY` — tylko odczyt. Jeśli wynik >= 0:

```text
call (int)dup2($in, 0)
call (int)close($in)
info inferiors
continue
```

**Zadania:**

1. Sprawdź w B cele 0 i 2 w /proc procesu oraz zawartość nowego stderr.
2. Znajdź na stdout komunikat `stdin: b'...'` z fragmentem prawdziwego stdin.txt.
   Program czyta do 64 bajtów na krok, więc treść może pojawić się w częściach.
3. Po obserwacji odłącz GDB (Ctrl+C, detach, quit) i zakończ własny proces po PID.

**Zaliczenie:** [ ] ten sam PID czyta dane z pliku i pisze stderr do nowego pliku.
Przy końcu stdin czytanie zwraca zero bajtów; nasz program mimo tego kontynuuje kroki.

<details>
<summary>Sprawdzenie</summary>

```bash
ls -l "/proc/$TARGET_PID/fd"
tail scratch/stderr-live.log
```

Ustaw TARGET_PID na PID tego nowego procesu. Wynik dup2 powinien być odpowiednio
2 i 0. STDOUT nadal trafia do terminala; dopiero osobna zmiana fd 1 zmieni jego cel.

</details>

## 4. IP, interfejs, port, klient i serwer

**Cel:** umiesz odróżnić adres maszyny od portu programu.
`127.0.0.1` to IPv4 loopback (ta sama maszyna/przestrzeń sieciowa),
`lo` to interfejs loopback. Port 8080 wybiera naszą usługę TCP.
Klient otwiera własny, zwykle tymczasowy port źródłowy.

| Komenda | Działanie i przydatne opcje |
|---|---|
| `ip -br addr` | Skrócona lista interfejsów i ich adresów; -br to brief. |
| `ip link show lo` | Stan interfejsu lo; nie zmienia konfiguracji. |
| `ip route` | Tablica tras; `ip route get 127.0.0.1` pokazuje wybór trasy do konkretnego adresu. |
| `ss -tlnp` | -t TCP, -l nasłuch, -n numery portów/adresów bez nazw usług, -p procesy. -a obejmuje też nasłuch, -e pokazuje dodatkowe dane, np. inode. |
| `nc -4 -v ADRES PORT` | Połączenie TCP: -4 IPv4, -v szczegóły. -w 5 limit czekania, -N zamyka kierunek wysyłania po końcu stdin. |

**Zadania:**

1. Odczytaj interfejsy i trasę do 127.0.0.1.
2. W terminalu A uruchom nasz serwer:

```bash
python3 -u server.py --bind 127.0.0.1 --port 8080 --duration 900
```

3. W B znajdź port poleceniem:

```bash
ss -tlnp 'sport = :8080'
```

**Zaliczenie:** [ ] widzisz LISTEN na 127.0.0.1:8080; serwer pozostaje uruchomiony
do działów 5–9. Jeśli port zajęty, wybierz np. 18080 i zmień go we wszystkich
dalszych komendach. Nie kończ obcego procesu zajmującego port.

<details>
<summary>Rozwiązanie części o adresach</summary>

```bash
ip -br addr
ip link show lo
ip route get 127.0.0.1
```

Brak uprawnień do netlink w kontenerze/sandboxie to ograniczenie środowiska,
nie dowód, że maszyna nie ma interfejsów. PID innych użytkowników może być ukryty.

</details>

## 5. Handshake TCP w tcpdump i stany w ss

**Cel:** zobaczyć SYN → SYN+ACK → ACK. To uzgodnienie TCP poprzedza żądanie HTTP.
Terminal A nadal obsługuje serwer. W B uruchom przechwytywanie lokalnego ruchu:

```bash
sudo tcpdump -i lo -nn -S -l 'tcp port 8080' | tee scratch/tcp.txt
```

| Argument tcpdump | Znaczenie |
|---|---|
| `-i lo` / `-i any` | Wybrany interfejs / wszystkie dostępne interfejsy. Lo wystarczy do lokalnego serwera. |
| `-nn` | Bez zamiany adresów i portów na nazwy. |
| `-S` | Pełne numery sekwencji; bez tej opcji kolejne są często względne. |
| `-l` | Buforowanie wierszowe, przydatne przy tee. |
| `-c N` | Zakończ po N pakietach; bez tej opcji kończysz Ctrl+C. |
| `-A` | Pokaż treść pakietów w ASCII; z HTTP zobaczysz tekst żądania. |
| `'tcp port 8080'` | Filtr przechwytywania, nie grep; obejmuje oba kierunki tego portu. |

W C otwórz połączenie i przez chwilę niczego nie wpisuj:

```bash
nc -4 -v 127.0.0.1 8080
```

W tcpdump zobaczysz wiersze z flagami (numery/adresy portu klienta będą inne):

```text
klient > serwer: Flags [S]     — SYN
serwer > klient: Flags [S.]    — SYN + ACK
klient > serwer: Flags [.]     — ACK
```

To opis formatu, nie zapis udający Twój pomiar. Kropka oznacza flagę ACK.
SYN zużywa jeden numer sekwencji: potwierdzenie zwykle ma wartość SYN.seq + 1.
ACK może też towarzyszyć danym; PSH (`P`) nie jest częścią samego handshake.

Gdy C nadal ma otwarte nc, w B przerwij tcpdump Ctrl+C i sprawdź:

```bash
ss -tnp '( sport = :8080 or dport = :8080 )'
ss -tn state syn-sent
```

| Stan | Co oznacza |
|---|---|
| LISTEN | Serwer czeka na nowe połączenia; to nie połączenie z konkretnym klientem. |
| SYN-SENT | Klient wysłał SYN i czeka na SYN+ACK. Na localhost etap jest bardzo krótki — ss zwykle go nie zdąży pokazać. |
| ESTABLISHED | Handshake zakończony, połączenie gotowe do przesyłania danych. Lokalnie zwykle zobaczysz oba końce jako dwa gniazda. |
| TIME-WAIT | Po aktywnym zamknięciu TCP jądro jeszcze przechowuje stan, m.in. dla opóźnionych segmentów i ponownego FIN. Nie musi już być PID. |

W C wyślij teraz żądanie z działu 6; serwer odpowie i zamknie połączenie.
Następnie w B:

```bash
ss -tan state time-wait '( sport = :8080 or dport = :8080 )'
```

**Zadania:** zaznacz we własnym tcp.txt trzy pakiety, odczytaj port klienta,
wyjaśnij trzy stany ze zrzutu i odnotuj, czy rzeczywiście widziałeś SYN-SENT.
**Zaliczenie:** [ ] masz własny handshake i ESTABLISHED; brak uchwyconego
SYN-SENT nie jest błędem. TIME-WAIT zależy od strony i sposobu zamknięcia;
sprawdzaj go od razu po normalnym żądaniu z Connection: close, nie po zabiciu nc.

<details>
<summary>Wariant port 80 z publiczną stroną</summary>

Po zakończeniu lokalnej próby uruchom przechwytywanie i klienta w osobnych oknach:

```bash
sudo tcpdump -i any -nn -S 'tcp port 80 and host neverssl.com'
```

```bash
nc -4 -v -w 10 neverssl.com 80
```

Filtr rozwiązuje domenę przy starcie; domena może mieć kilka adresów, które
zmieniają się w czasie. W razie braku zgodnego ruchu porównaj adres nc z filtrem.
Zatrzymaj capture po własnej próbie. Dalej wyślij GET z Host: neverssl.com.

</details>

## 6. Ręczna rozmowa HTTP: nc, GET, Host i curl

**Cel:** zobaczyć, że HTTP/1.1 jest tekstowym protokołem ponad TCP.
Żądanie zawiera linię metody/ścieżki/wersji, nagłówki i pustą linię.
Host wskazuje nazwę/port usługi; jeden adres IP może obsługiwać wiele witryn.

W nc z działu 5 wpisz poniższe i naciśnij Enter również po ostatnim nagłówku,
aby wysłać pustą linię. Nasz lokalny serwer toleruje LF podczas ręcznego pisania;
protokół wymaga zakończeń CRLF, które poprawnie tworzy printf w rozwiązaniu.

```http
GET / HTTP/1.1
Host: localhost:8080
Connection: close

```

| Komenda / opcja | Jak działa |
|---|---|
| `printf '...\r\n'` | Formatuje tekst; \r\n to CRLF. Podwójne CRLF kończy nagłówki. Jest dokładniejsze niż echo -e. |
| `nc -N -w 5 127.0.0.1 8080` | Łączy się z serwerem; -N po EOF stdin zamyka kierunek wysyłania, nadal pozwalając odebrać odpowiedź. -w ogranicza czekanie. |
| `curl -v URL` | Wykonuje HTTP; -v pokazuje szczegóły, żądanie `>` i odpowiedź `<` na stderr. Body jest na stdout. |
| `curl -i URL` | Nagłówki odpowiedzi razem z body na stdout. |
| `curl -I URL` | Wysyła HEAD zamiast GET: nagłówki odpowiedzi bez body. |
| `--http1.1`, `--noproxy '*'` | Wymusza HTTP/1.1 i omija proxy z konfiguracji środowiska dla tej komendy. |
| `-D plik`, `-o plik`, `--max-time 5` | Zapis nagłówków, zapis body, limit czasu całej operacji. |

**Zadania:**

1. Wyślij ręczny GET, zapisz odpowiedź; wskaż status, nagłówki i body.
2. Wyślij żądania do /health i /nie-ma. Odczytaj 200 oraz 404.
3. Porównaj z curl -v; zapisz body i diagnostykę osobno.
4. Wyjaśnij nagłówki odpowiedzi:

| Element odpowiedzi | Znaczenie |
|---|---|
| `HTTP/1.1 200 OK` | Wersja i kod sukcesu. `404 Not Found` oznacza nieistniejącą ścieżkę. |
| `Server` | Informacja deklarowana przez oprogramowanie serwera. |
| `Date` | Czas utworzenia odpowiedzi, zwykle w GMT. |
| `Content-Type` | Rodzaj treści i kodowanie tekstu. |
| `Content-Length` | Liczba bajtów body, nie liczba znaków. Przy HEAD opisuje długość odpowiadającego GET. |
| `Connection: close` | Po odpowiedzi połączenie zostanie zamknięte. |
| `X-Lab` | Nasz własny nagłówek dydaktyczny; nie jest obowiązkowym polem HTTP. |

**Zaliczenie:** [ ] odróżniasz HTTP od TCP; masz GET/200, GET/404 i porównanie curl.

<details>
<summary>Rozwiązanie i publiczny wariant</summary>

```bash
printf 'GET / HTTP/1.1\r\nHost: localhost:8080\r\nConnection: close\r\n\r\n' | nc -N -w 5 127.0.0.1 8080 | tee scratch/http-nc.txt
curl --noproxy '*' --http1.1 --max-time 5 -v http://127.0.0.1:8080/ > scratch/body.html 2> scratch/curl-v.txt
curl --noproxy '*' -i http://127.0.0.1:8080/health
curl --noproxy '*' -i http://127.0.0.1:8080/nie-ma
```

Polecenie curl może mieć kod 0 także dla HTTP 404: sam transfer się udał.
Opcja -f powoduje niezerowy kod dla odpowiedzi HTTP od 400.

```bash
printf 'GET / HTTP/1.1\r\nHost: neverssl.com\r\nConnection: close\r\n\r\n' | nc -N -w 10 neverssl.com 80
curl --noproxy '*' --http1.1 --max-time 15 -v http://neverssl.com/
```

Jeśli sieć wymaga proxy lub blokuje port 80, lokalna część nadal działa.
Https na 443 wymaga TLS: samo nc nie zastępuje klienta TLS.

</details>

## 7. DNS: hosts, resolv.conf, systemd-resolved i dig

**Cel:** rozumiesz, jak nazwa neverssl.com zamienia się w adres IP.
DNS nie jest wymagany, gdy łączysz się bezpośrednio z 127.0.0.1.

| Plik / narzędzie | Rola |
|---|---|
| `/etc/hosts` | Lokalne przypisania nazw do adresów. Nie jest globalną bazą DNS. |
| `/etc/nsswitch.conf`, wpis hosts | Kolejność źródeł rozwiązywania nazw w systemie (np. files, dns, resolve). |
| `/etc/resolv.conf` | Konfiguracja resolvera: m.in. nameserver i search. Często dowiązanie do pliku zarządzanego przez usługę. |
| `systemd-resolved` | Lokalna usługa resolvera, może mieć cache i DNS osobno na interfejsach. 127.0.0.53 zwykle oznacza lokalny stub, nie publiczny serwer upstream. Nie każdy system jej używa. |
| `getent ahostsv4 nazwa` | Rozwiązuje nazwę przez systemową konfigurację NSS; może uwzględnić hosts. |
| `dig nazwa A` | Pyta DNS o rekord A (IPv4). Dig sam nie interpretuje hosts jako źródła rekordów, ale może pytać resolver, który je uwzględnia. |

**Rekurencja:** klient prosi resolver „daj końcowy wynik”, a resolver korzysta
z cache lub sam odpytuje potrzebne serwery. **Iteracja:** pytający dostaje
odsyłacz do kolejnego serwera i sam kontynuuje, np. root → .com → autorytatywny.
Dig +trace wykonuje takie kolejne zapytania; to nie pomiar trasy pakietów jak traceroute.

| Argument dig | Znaczenie |
|---|---|
| `A`, `AAAA`, `NS` | Typ: adres IPv4, IPv6, serwery nazw. |
| `+short` | Skrócony wynik; wygodny, ale ukrywa diagnostykę. |
| `@SERWER` | Wybiera konkretny serwer DNS, zamiast domyślnego z konfiguracji. |
| `+trace` | Śledzi delegacje zapytaniami iteracyjnymi od korzenia. |
| `-4`, `+nodnssec` | Tylko transport IPv4; pominięcie prośby o dodatkowe rekordy DNSSEC, aby uprościć widok ćwiczenia. Nie jest to test poprawności podpisów DNSSEC. |
| `+norecurse` | Nie prosi danego serwera o rekurencję; samo w sobie nie odtwarza całego +trace. |
| `+time=2 +tries=1` | Ogranicza czekanie i ponawianie zapytań; całe +trace może nadal obejmować wiele kroków. |

**Zadania:**

1. Odczytaj hosts, cel resolv.conf, wpis hosts z nsswitch oraz nameserver.
2. Sprawdź systemd-resolved poleceniem resolvectl status, jeśli jest dostępne.
3. Zapytaj dig o neverssl.com A; odczytaj ANSWER, SERVER i flagi rd/ra.
   Rd oznacza żądanie rekurencji, ra dostępność rekurencji; nie dowodzą cache miss.
4. Zapisz dig +trace i wskaż poziomy delegacji albo pełny komunikat blokady.
5. Porównaj getent localhost z dig localhost. Wyjaśnij, czemu mogą się różnić.

**Zaliczenie:** [ ] rozróżniasz NSS od zapytania DNS oraz rekurencję od iteracji.
Port 53 do zewnętrznych serwerów może być blokowany: wtedy działający zwykły dig
nie gwarantuje działającego +trace. Nie zmieniaj hosts/resolv.conf do tych ćwiczeń.

<details>
<summary>Rozwiązanie</summary>

```bash
cat /etc/hosts
readlink -f /etc/resolv.conf
cat /etc/resolv.conf
grep '^hosts:' /etc/nsswitch.conf
resolvectl status
dig neverssl.com A +time=2 +tries=1
dig neverssl.com A +short
dig -4 +trace neverssl.com A +nodnssec +time=2 +tries=1 | tee scratch/dns-trace.txt
getent ahostsv4 localhost
dig localhost A +time=2 +tries=1
```

Rekordy/adresy zmieniają się w czasie — zapisuj własne wyniki, nie oczekuj jednej
stałej liczby. Brak resolvectl/usługi w kontenerze też jest poprawną obserwacją.

</details>

## 8. Strace: jakie wywołania wykonuje curl

**Cel:** powiązać żądanie HTTP z operacjami jądra. Strace obserwuje **wywołania
systemowe procesu**, tcpdump **pakiety na interfejsie**. Jedno wywołanie zapisu
nie musi oznaczać jednego pakietu, a read/recv może oddać tylko fragment odpowiedzi.

| Komenda / opcja | Działanie |
|---|---|
| `strace komenda` | Uruchamia własny proces pod śledzeniem; zwykle bez sudo. |
| `-e trace=network` | Tylko grupa wywołań sieciowych; zapis %network jest również obsługiwany. |
| `-e trace=network,read,write,close` | Dodatkowo read/write/close; ważne, bo aplikacja może używać ich do gniazd zamiast sendto/recvfrom. |
| `-f` | Śledzi także potomków/wątki uruchomionego procesu. |
| `-s 256` | Pokazuje do 256 bajtów argumentów tekstowych; nie zmienia żądania HTTP. |
| `-o plik` | Zapis śladu do pliku zamiast mieszania go z stderr programu. |
| `-yy` | Dodaje szczegóły deskryptorów, np. adresy końców gniazda. |

Z uruchomionym lokalnym serwerem:

```bash
strace -f -s 256 -yy -o scratch/curl-network.trace -e trace=network curl --noproxy '*' --http1.1 --max-time 5 http://127.0.0.1:8080/health
```

**Zadania:**

1. Znajdź socket, connect oraz sendto/recvfrom, jeśli występują.
2. Zidentyfikuj adres/port connect i bufor zawierający GET albo odpowiedź.
3. Powtórz z filtrem network,read,write,close. Dlaczego pokazuje więcej?
4. Powtórz dla neverssl.com, jeśli masz sieć. Oddziel połączenia DNS od HTTP.

| Wywołanie | Związek z rozmową |
|---|---|
| `socket(...)` | Tworzy gniazdo i zwraca fd; jeszcze nie nawiązuje połączenia. |
| `connect(fd, adres, ...)` | Inicjuje połączenie TCP; handshake realizuje stos TCP jądra. |
| `sendto` / `sendmsg` / `write` | Wysyła bajty, np. żądanie GET. Sendto może być używane także z połączonym TCP — nazwa nie oznacza wyłącznie UDP. |
| `recvfrom` / `recvmsg` / `read` | Odbiera bajty odpowiedzi. Zero po odczytaniu danych może oznaczać normalny koniec strumienia. |
| `close(fd)` | Zwalnia deskryptor; TCP może utrzymywać TIME-WAIT po zakończeniu procesu. |

Connect może zwrócić `EINPROGRESS` przy nieblokującym gnieździe. To nie musi być
błąd końcowy: aplikacja później sprawdza gotowość i np. SO_ERROR.

**Zaliczenie:** [ ] masz własny ślad i umiesz przypisać do niego kroki rozmowy nc.
Nie dopisuj brakującego recvfrom do raportu — wskaż rzeczywiście użyte read/recv.

<details>
<summary>Rozwiązanie</summary>

```bash
grep -E 'socket\(|connect\(|sendto\(|recvfrom\(' scratch/curl-network.trace
strace -f -s 256 -yy -o scratch/curl-full.trace -e trace=network,read,write,close curl --noproxy '*' --http1.1 --max-time 5 http://127.0.0.1:8080/health
strace -f -s 256 -yy -o scratch/public-network.trace -e trace=network curl --noproxy '*' --http1.1 --max-time 15 http://neverssl.com/
```

Adres IP lokalnego URL omija DNS, ale biblioteka może dodatkowo sprawdzać lokalne
gniazda/usługi. W sandboxie ptrace może być blokowane — wykonaj na własnym hoście.

</details>

## 9. Port nasłuchujący → PID → /proc; 127.0.0.1 a 0.0.0.0

**Cel:** powiązać usługę z procesem. Wpis LISTEN opisuje gniazdo oczekujące;
ESTABLISHED opisuje już utworzone połączenie klient–serwer.

```bash
ss -tlnp 'sport = :8080'
ss -tlnep 'sport = :8080'
```

**Zadania:**

1. Odczytaj pid=... własnego serwera i wstaw go do zmiennej SERVER_PID w B.
2. Zobacz jego polecenie, plik wykonywalny i otwarte deskryptory.
3. Dopasuj `ino:...` z ss -e do `socket:[...]` w /proc/PID/fd.
   Nie zakładaj stałego numeru fd — serwer może go przydzielić inaczej.
4. Wyjaśnij różnicę między bind 127.0.0.1 a 0.0.0.0 bez zmieniania bind serwera.

| Adres nasłuchu IPv4 | Znaczenie |
|---|---|
| `127.0.0.1:8080` | Tylko loopback tej przestrzeni sieciowej; inny komputer nie połączy się przez Twój adres LAN. |
| `0.0.0.0:8080` | Wszystkie lokalne adresy IPv4; dostęp z zewnątrz zależy jeszcze od firewalla, routingu i NAT. To adres wiązania, nie docelowy adres do wpisania w kliencie. |

W kontenerze 127.0.0.1 oznacza kontener, a nie automatycznie hosta.
Nasłuch na wszystkich interfejsach nie oznacza, że firewall przepuszcza połączenia.

**Zaliczenie:** [ ] pokazałeś port, jego PID i ten sam inode gniazda w dwóch widokach.
Do pokazania procesów innych użytkowników ss -p może wymagać sudo; nasz serwer
uruchamiasz na własnym koncie. Nie trzeba publikować go na 0.0.0.0.

<details>
<summary>Rozwiązanie</summary>

```bash
SERVER_PID=WPISZ_PID_Z_SS
ps -p "$SERVER_PID" -o pid,etime,args
readlink "/proc/$SERVER_PID/exe"
tr '\0' ' ' < "/proc/$SERVER_PID/cmdline"
printf '\n'
ls -l "/proc/$SERVER_PID/fd"
```

Cmdline oddziela argumenty bajtem NUL; tr zastępuje go spacją do wyświetlenia.
Nie myl socketu nasłuchującego z innym socketem tego samego procesu.

</details>

## 10. Dokumentacja man do PDF

**Cel:** wykonać konwersję ze zrzutu i rozumieć potok.
`man -t ps` formatuje dokumentację do PostScript, `ps2pdf - wynik.pdf`
czyta ten strumień ze stdin i tworzy PDF. Myślnik tutaj oznacza wejście standardowe.
Nie uruchamiasz ps — przetwarzasz jego instrukcję.

```bash
man -t ps | ps2pdf - scratch/ps.pdf
```

**Zadania:**

1. Przed potokiem włącz `set -o pipefail`, aby zauważyć także błąd man.
2. Utwórz ps.pdf oraz dokumentację ss jako ss.pdf.
3. Jeśli masz `man gcc`, zrób także gcc.pdf; brak tej strony oznacz jako brak
   dokumentacji, nie jako błąd ps2pdf. Dokumentacja gcc nie wszędzie jest instalowana.
4. Otwórz wygenerowany PDF w przeglądarce dokumentów i sprawdź czytelność.

**Zaliczenie:** [ ] masz czytelne PDF-y ps i ss. Samo istnienie pliku nie dowodzi
poprawności treści. Na Ubuntu ps2pdf pochodzi z ghostscript, man -t wymaga groff.
Polecenie pacman ze zrzutu jest dla Arch Linux; na Ubuntu użyj apt z działu 0.

<details>
<summary>Rozwiązanie</summary>

```bash
set -o pipefail
man -t ps | ps2pdf - scratch/ps.pdf
man -t ss | ps2pdf - scratch/ss.pdf
ls -lh scratch/*.pdf
```

To tworzenie dokumentacji narzędzi, nie eksport kodu programu ps/ss.

</details>

## 11. Mini-projekt: przygotuj własny raport do zadań

Skopiuj szablon i uzupełnij go własnymi pomiarami. Cp kopiuje plik;
-n zapobiega nadpisaniu istniejącego raportu.

```bash
cp -n REPORT_TEMPLATE.md scratch/moj-raport.md
```

Raport ma zawierać: PID i fd przed/po, handshake, stany TCP, ręczne HTTP,
objaśnienia nagłówków, DNS, wybrane syscalle oraz powiązanie portu z PID i inode.
Nie wpisuj, że zobaczyłeś stan/wywołanie, którego nie ma w Twoich pomiarach.
Zapisy packet capture lub konfiguracji zostaw lokalnie w scratch/.

**Sprzątanie:** zakończ nc i tcpdump przez Ctrl+C w ich terminalach, serwer
przez Ctrl+C w A. Proces odłączony od GDB zakończ dopiero po dowodzie zmiany,
używając jego zapisanego PID. Sprawdź ss, czy Twój serwer już nie nasłuchuje.
Nie kończ innych usług systemowych.

**Zaliczenie:** [ ] raport opisuje wszystkie punkty zrzutu i uczciwie podaje
ograniczenia; własne procesy są zakończone. Czytanie rozwiązań nie zastępuje wykonania.

## Źródła i weryfikacja

Mechanizm deskryptorów: [Linux /proc/PID/fd](https://man7.org/linux/man-pages/man5/proc_pid_fd.5.html)
i [dup2](https://man7.org/linux/man-pages/man2/dup2.2.html).
GDB: [attach/detach](https://www.sourceware.org/gdb/current/onlinedocs/gdb.html/Attach.html),
[wywoływanie funkcji](https://www.sourceware.org/gdb/current/onlinedocs/gdb.html/Calling.html)
i [Yama](https://cdn.kernel.org/doc/html/latest/admin-guide/LSM/Yama.html).
Sieć: [ss](https://man7.org/linux/man-pages/man8/ss.8.html),
[tcpdump](https://man7.org/linux/man-pages/man8/tcpdump.8.html),
[curl](https://curl.se/docs/manpage.html),
[dig/BIND](https://bind9.readthedocs.io/en/v9.18.42/manpages.html)
i [HTTP/1.1](https://www.rfc-editor.org/rfc/rfc9112.html).
Do szczegółów wariantów systemowych używaj lokalnego man nazwa oraz --help.

Testy dołączonych programów uruchom z tego katalogu:

```bash
python3 -m unittest discover -s tests -v
```

To sprawdza programy laboratoryjne, nie zalicza za Ciebie zadań GDB/tcpdump/DNS.

Podczas przygotowania (2026-11-06) przeszło 9 testów, sprawdzono GDB ze zmianą
fd 0/1/2 w tym samym PID, lokalne nc/curl/strace, LISTEN/ESTABLISHED/TIME-WAIT,
powiązanie inode z /proc, publiczne HTTP, zapytanie DNS i pełne dig +trace.
Utworzono także PDF dokumentacji ps i ss. Przechwytywanie pakietów tcpdump
pozostaje do ręcznego wykonania — na tym hoście sudo wymaga hasła administratora.
