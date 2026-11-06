# Linux: procesy, deskryptory i sieć — kurs do zadań 9 i 10

Ten kurs prowadzi od podstaw do wszystkich punktów z przesłanego zrzutu.
Każdy dział ma wyjaśnienie, argumenty komend, zadania i rozwijane rozwiązanie.
Pracuj w Bash na Ubuntu, po jednym dziale; całość to około 3–5 godzin.
Potrzebujesz dwóch, czasami trzech okien terminala na tej samej maszynie.

**Zadanie 9:** dokładnie jak na zrzucie — uruchamiasz `sleep 1000 &`, a potem
zmieniasz stdout tego już działającego procesu na `/tmp/foo`, zachowując PID.
**Zadanie 10:** używasz wyłącznie dołączonego serwera `http://127.0.0.1:8080/`
(lub `http://localhost:8080/`). Wszystkie połączenia HTTP i pomiary TCP są lokalne.
DNS omawiamy na nazwie localhost; jej szczególne zachowanie wyjaśnia dział 7.

| Część zrzutu | Działy kursu |
|---|---|
| 9: stdout działającego sleep → /tmp/foo | 1–3 |
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

Do zadania 9 potrzebujesz systemowego programu sleep i GDB. Zadanie 10 korzysta
z `server.py`, który udostępnia `web/index.html`, `/health` i odpowiedzi 404.
Serwer działa na stdlib Pythona i kończy się domyślnie po 900 sekundach.
Nie wymaga Docker ani innych usług. Starsze pliki `io_demo.py` i `stdin.txt`
zostają jako opcjonalny materiał; nie są częścią zadania 9.

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

## 1. Zadanie 9: uruchom sleep i sprawdź deskryptory

**Cel:** otrzymać stan początkowy taki jak na obrazku. Sleep przez 1000 sekund
czeka, niczego normalnie nie wypisując. Mimo to ma stdout — otwarty deskryptor 1.

Każdy proces ma własną tabelę deskryptorów: 0 to zwykle stdin, 1 stdout, 2 stderr.
`/proc/PID/fd` pokazuje je jako dowiązania. To widok informacji jądra, nie zwykłe
pliki zapisane na dysku. `/dev/pts/N` oznacza pseudoterminal; N zależy od Twojej sesji.

| Polecenie | Co robi i przydatne argumenty |
|---|---|
| `sleep 1000 &` | Uruchamia sleep w tle; 1000 to sekundy, & oddaje terminal. Bez początkowego przekierowania stdout pozostaje terminalem. |
| `SLEEP_PID=$!` | Zapamiętuje PID ostatnio uruchomionego zadania w tle. Wpisz od razu po sleep. |
| `ls -l /proc/PID/fd` | -l pokazuje szczegóły i cele dowiązań. |
| `readlink /proc/PID/fd/1` | Wypisuje sam cel stdout. |
| `ps -p PID -o pid,stat,etime,args` | Wybiera proces i kolumny: PID, stan, czas życia, polecenie. |

W **interaktywnym terminalu A**:

```bash
sleep 1000 &
SLEEP_PID=$!
echo "$SLEEP_PID"
ls -l "/proc/$SLEEP_PID/fd"
ps -p "$SLEEP_PID" -o pid,stat,etime,args
```

Zobaczysz rzeczywisty PID — nie musi wynosić 4096 jak na zrzucie. Oczekiwany
schemat dowiązań (numer terminala zależy od Twojego środowiska):

```text
0 -> /dev/pts/N
1 -> /dev/pts/N
2 -> /dev/pts/N
```

**Zadania:** zapisz PID i cele fd 0/1/2 do własnej notatki. Zachowaj ten sleep
uruchomiony do końca działu 3. Nie wykonuj kill, nie uruchamiaj drugiego sleep
jako zamiennika i nie dodawaj `> /tmp/foo` do polecenia startowego.

**Zaliczenie:** [ ] istnieje Twój proces sleep 1000, a fd 1 początkowo wskazuje
terminal. Powyższy stan zakłada normalny interaktywny shell; uruchomienie w skrypcie
lub przez potok może dać inne cele fd 0/1/2.

## 2. Zadanie 9: dołącz GDB i zmień stdout na /tmp/foo

**Cel:** zmienić tabelę deskryptorów już działającego sleep. Zapis
`echo tekst > /proc/PID/fd/1` tego nie robi: tylko zapisuje do obecnego celu.
GDB wykona w procesie sleep trzy funkcje libc:

1. `open` otworzy `/tmp/foo` i zwróci dodatkowy deskryptor.
2. `dup2(nowy, 1)` podstawi otwarty plik pod numer 1, zamykając dotychczasowy fd 1.
3. `close(nowy)` zamknie dodatkowy numer; kopia pod numerem 1 zostanie otwarta.

Debugger na chwilę wstrzyma proces. Nie kończy go ani nie uruchamia ponownie.
Nie zmieniamy fd 0 ani fd 2.

### Krok A: dołącz do istniejącego procesu

W tym samym terminalu A (zmienna SLEEP_PID nadal jest w jego shellu):

```bash
gdb -q -p "$SLEEP_PID"
```

`-q` pomija baner, `-p` oznacza attach do podanego PID. **Nie wpisuj run** — run
uruchamiałoby nowy program, a tu pracujesz na już istniejącym sleep.

Na Ubuntu Yama może blokować attach z osobnego procesu, mimo że sleep należy do
Ciebie. Jeśli dostaniesz `ptrace: Operation not permitted`, wyjdź z GDB przez quit
i dołącz do **tego samego, nadal działającego sleep**:

```bash
sudo gdb -q -p "$SLEEP_PID"
```

Ten wariant wymaga uprawnień administratora i hasła. Nie zmieniaj ptrace_scope
przez sysctl. Kontener/seccomp lub bardziej restrykcyjna polityka mogą blokować
attach również z sudo — wtedy wykonaj ćwiczenie na swoim hoście/VM.

### Krok B: otwórz plik wewnątrz sleep

Poniższe wpisujesz **w GDB**, nie w Bash:

```text
info inferiors
set $out = (int)open("/tmp/foo", 1089, 0600)
print $out
```

| Element | Znaczenie |
|---|---|
| `info inferiors` | Pokazuje debugowany proces; PID ma zgadzać się z SLEEP_PID. |
| `set $out = ...` | Zmienna samego GDB, nie Basha. Zapamiętuje deskryptor zwrócony przez open. |
| `(int)` | Podaje GDB typ wyniku, potrzebny przy braku symboli debugowania funkcji libc. |
| `1089` | Linuxowe flagi `O_WRONLY | O_CREAT | O_APPEND`: 1 + 64 + 1024. Otwórz do zapisu, utwórz jeśli brak, dopisuj. |
| `0600` | Ósemkowe uprawnienia dla nowego pliku: odczyt/zapis właściciela. Istniejący plik zachowuje dotychczasowe uprawnienia. |

**Sprawdź wynik.** Nieujemny numer, np. 3, oznacza sukces. Przy -1 nie wykonuj
kolejnego kroku; sprawdź uprawnienia i komunikat. Użycie sudo może utworzyć plik
będący własnością procesu sleep — open wykonuje się w sleep, nie w samym GDB.
Wybrano dopisywanie, aby nie zerować ewentualnej istniejącej zawartości `/tmp/foo`.

### Krok C: podmień fd 1 i odłącz debugger

```text
call (int)dup2($out, 1)
call (int)close($out)
detach
quit
```

| Komenda | Oczekiwany wynik i znaczenie |
|---|---|
| `call (int)dup2($out, 1)` | Wynik 1: stdout wskazuje już otwarty plik. Przy -1 nie deklaruj sukcesu. |
| `call (int)close($out)` | Wynik 0: zamknięty dodatkowy deskryptor; fd 1 nadal wskazuje plik. |
| `detach` | Wznawia i odłącza istniejący sleep; PID się nie zmienia. |
| `quit` | Zamyka GDB; po detach nie kończy procesu sleep. |

Nie potrzebujesz continue przed detach — detach sam pozwala procesowi działać
samodzielnie. Nie używaj w GDB polecenia kill. Przy błędach wywołania funkcji,
ptrace lub rejestrów zachowaj pełny komunikat i sprawdź stan procesu; sam exit 0
programu gdb nie dowodzi sukcesu zmiany.

**Zadania:** wykonaj kroki A–C na sleep z działu 1 i zapisz wyniki open, dup2, close.
**Zaliczenie:** [ ] debugger odłączył się od tego samego procesu bez jego restartu.
Ostateczny dowód sprawdzisz w kolejnym dziale.

## 3. Zadanie 9: porównaj /proc przed i po

W terminalu A, po wyjściu z GDB:

```bash
ls -l "/proc/$SLEEP_PID/fd"
readlink "/proc/$SLEEP_PID/fd/1"
ps -p "$SLEEP_PID" -o pid,stat,etime,args
```

**Oczekiwany schemat dokładnie jak na obrazku:**

```text
0 -> /dev/pts/N
1 -> /tmp/foo
2 -> /dev/pts/N
```

**Zadania:**

1. Porównaj z pierwszym ls: fd 1 ma nowy cel, a 0 i 2 pozostały bez zmian.
2. Potwierdź, że ps pokazuje ten sam PID i polecenie sleep 1000.
3. Wyjaśnij, dlaczego plik /tmp/foo może mieć rozmiar zero.
4. Dopiero po zapisaniu dowodów zakończ własny sleep:

```bash
kill "$SLEEP_PID"
```

**Zaliczenie:** [ ] ten sam sleep, fd 1 → /tmp/foo, bez kończenia procesu podczas
zmiany. Sleep normalnie niczego nie wypisuje — **pusty plik jest poprawnym wynikiem**.
Nie trzeba tworzyć sztucznych komunikatów ani używać tail -f. Nie usuwaj /tmp/foo,
jeśli istniał przed Twoim ćwiczeniem; wynik zadania to przede wszystkim dowiązania /proc.

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
<summary>Rozwiązanie na lokalnym serwerze</summary>

```bash
printf 'GET / HTTP/1.1\r\nHost: localhost:8080\r\nConnection: close\r\n\r\n' | nc -N -w 5 127.0.0.1 8080 | tee scratch/http-nc.txt
curl --noproxy '*' --http1.1 --max-time 5 -v http://127.0.0.1:8080/ > scratch/body.html 2> scratch/curl-v.txt
curl --noproxy '*' -i http://127.0.0.1:8080/health
curl --noproxy '*' -i http://127.0.0.1:8080/nie-ma
```

Polecenie curl może mieć kod 0 także dla HTTP 404: sam transfer się udał.
Opcja -f powoduje niezerowy kod dla odpowiedzi HTTP od 400.

Do tego zadania nie łączysz się z publiczną stroną. Lokalny serwer używa zwykłego
HTTP na 8080, więc nie potrzebujesz TLS ani portu 80. Nazwa localhost zwykle
rozwiązuje się do loopback; adres 127.0.0.1 wymusza używany tutaj wariant IPv4.

</details>

## 7. DNS i localhost: hosts, resolv.conf, dig

**Cel:** zrozumieć różnicę między nazwą localhost a adresem 127.0.0.1.
Wszystkie żądania HTTP nadal kierujesz do własnego serwera. Adres liczbowy omija
rozwiązywanie nazwy; localhost jest nazwą specjalną wskazującą loopback.

| Plik / narzędzie | Rola |
|---|---|
| `/etc/hosts` | Lokalne przypisania nazw do adresów, np. 127.0.0.1 localhost. Nie jest globalną bazą DNS. |
| `/etc/nsswitch.conf`, wpis hosts | Określa źródła i kolejność systemowego rozwiązywania nazw, np. files, dns, resolve. |
| `/etc/resolv.conf` | Konfiguracja resolvera DNS, m.in. nameserver. Może być dowiązaniem zarządzanym przez usługę. |
| `systemd-resolved` | Lokalna usługa resolvera; na Ubuntu stub często słucha na 127.0.0.53. Może syntetyzować odpowiedź localhost. Nie każdy system używa tej usługi. |
| `getent ahostsv4 localhost` | Rozwiązuje nazwę przez systemowe NSS, uwzględniając jego źródła, np. hosts. |
| `dig @127.0.0.53 localhost A` | Jawne zapytanie DNS do lokalnego stuba. Działa tylko, jeśli taki resolver jest uruchomiony. Dig nie odczytuje hosts samodzielnie. |

**Ważna granica ćwiczenia:** localhost nie ma zwykłej publicznej delegacji.
Nie da się uczciwie pokazać dla niego globalnego łańcucha root → TLD → domena.
Dlatego `dig +trace` omawiamy tutaj, ale nie wykonujemy zapytań do publicznych
serwerów DNS. Lokalny serwer HTTP na 8080 nie jest serwerem DNS; nie kieruj dig
na jego port. To świadome dostosowanie punktu DNS ze zrzutu do Twojego lokalnego labu.

**Rekurencja:** klient prosi resolver o końcową odpowiedź, a resolver korzysta
z cache lub odpytuje inne serwery. **Iteracja:** pytający dostaje odsyłacze
i sam odpytuje kolejne poziomy. `dig +trace nazwa` realizuje taki łańcuch dla
nazwy z rzeczywistymi delegacjami. Nie jest to traceroute i nie pokazuje tras IP.
Szybka lokalna odpowiedź localhost nie jest dowodem takiej rekurencji ani iteracji.

| Argument dig | Znaczenie |
|---|---|
| `@SERWER` | Wybiera serwer DNS; tu jawnie lokalny adres, aby nie pytać publicznego resolvera. |
| `A`, `AAAA` | Typ rekordu: IPv4 lub IPv6. |
| `+short` | Krótki wynik bez większości diagnostyki. |
| `+norecurse` | Nie prosi resolvera o rekurencję; nie zmienia zapytania w pełny +trace. |
| `+time=2 +tries=1` | Ogranicza czekanie i ponawianie próby. |

**Zadania:**

1. Odczytaj hosts, cel resolv.conf i wpis hosts z nsswitch.
2. Sprawdź getent localhost i porównaj z liczbowym URL.
3. Jeśli systemd-resolved działa na 127.0.0.53, zapytaj ten lokalny adres o localhost.
   Odczytaj ANSWER i SERVER. Przy braku lokalnego resolvera zapisz to ograniczenie;
   nie podstawiaj publicznego DNS i nie zmieniaj konfiguracji systemu.
4. Porównaj odpowiedzi A i AAAA. Nasz serwer nasłuchuje tylko na 127.0.0.1,
   więc IPv6 ::1 nie jest jego adresem nasłuchu; curl -4 wybiera IPv4.
5. Wyjaśnij rekurencję, iterację i dlaczego +trace localhost nie realizuje
   publicznego łańcucha delegacji.

**Zaliczenie:** [ ] rozróżniasz NSS od DNS i wyjaśniasz wyjątkowość localhost.
Brak lokalnego serwera DNS nie przeszkadza w ćwiczeniach HTTP po 127.0.0.1.
Nie opisuj części teoretycznej +trace jako wykonanego pomiaru.

<details>
<summary>Rozwiązanie lokalne</summary>

```bash
cat /etc/hosts
readlink -f /etc/resolv.conf
cat /etc/resolv.conf
grep '^hosts:' /etc/nsswitch.conf
getent ahostsv4 localhost
resolvectl status
dig @127.0.0.53 localhost A +time=2 +tries=1
dig @127.0.0.53 localhost AAAA +time=2 +tries=1
curl --noproxy '*' -4 --max-time 5 http://localhost:8080/health
curl --noproxy '*' --max-time 5 http://127.0.0.1:8080/health
```

Brak resolvectl/usługi lokalnej jest poprawną obserwacją. Dig wykonaj wyłącznie
po potwierdzeniu dostępności lokalnego resolvera; w innych środowiskach jego adres
może być inny. Sam getent nie musi wygenerować żadnego pakietu DNS.

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
4. Powtórz dla http://localhost:8080/health z curl -4. Porównaj z liczbowym
   adresem: rozwiązywanie localhost może skończyć się lokalnie, bez pakietu DNS.

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
strace -f -s 256 -yy -o scratch/localhost-network.trace -e trace=network curl --noproxy '*' -4 --http1.1 --max-time 5 http://localhost:8080/health
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
przez Ctrl+C w A. Sleep odłączony od GDB zakończ dopiero po dowodzie zmiany,
używając zapisanego SLEEP_PID (jeśli jeszcze działa po dziale 3). Sprawdź ss, czy Twój serwer już nie nasłuchuje.
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

Programy laboratoryjne mają 9 testów. Nie zastępują one wykonania attach do sleep
z zadania 9. Przechwytywanie tcpdump oraz attach wymagający sudo wykonujesz ręcznie,
jeśli system wymaga hasła administratora. HTTP i pomiary TCP korzystają wyłącznie
z lokalnego serwera; część +trace to wyjaśnienie ograniczenia localhost.
