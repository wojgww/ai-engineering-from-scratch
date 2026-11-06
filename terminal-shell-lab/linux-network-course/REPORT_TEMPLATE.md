# Raport: deskryptory procesu i sieć

Data: do uzupełnienia. Środowisko (host/VM/kontener): do uzupełnienia.
Polecenia wykonane samodzielnie i ograniczenia: do uzupełnienia.

## Zadanie 9 — stdout działającego sleep 1000 → /tmp/foo

- Polecenie startowe sleep 1000 &; PID przed i po zmianie:
- Cel fd 0/1/2 przed zmianą:
- Dokładne komendy GDB, wyniki open/dup2/close:
- Cel fd 1 po zmianie (/tmp/foo); potwierdzenie, że fd 0 i 2 się nie zmieniły:
- Dlaczego pusty /tmp/foo jest poprawny (sleep nie wypisuje danych):
- Dlaczego zapis do /proc/PID/fd/1 nie zastępuje dup2:
- Jeśli coś nie zadziałało: pełny komunikat, bez deklarowania wykonania:

## Zadanie 10 — TCP/HTTP/DNS i procesy

### 1. Handshake i stany TCP

- Adresy, porty i trzy wiersze SYN/SYN+ACK/ACK z własnego tcpdump:
- ESTABLISHED, TIME-WAIT oraz wyjaśnienie SYN-SENT:
- Czy faktycznie zobaczono SYN-SENT, czy wyjaśniono go teoretycznie:

### 2. Ręczne HTTP i curl — 127.0.0.1:8080

- Żądanie wysłane przez nc:
- Status i nagłówki odpowiedzi oraz ich znaczenie:
- Porównanie z curl -v:

### 3. DNS

- Lokalna nazwa localhost: wynik getent oraz zapytania do lokalnego resolvera, jeśli dostępny:
- Rola hosts, resolv.conf i systemd-resolved na tej maszynie:
- Rekurencja a iteracja; dlaczego localhost nie ma publicznego łańcucha dig +trace (część teoretyczna):

### 4. Wywołania systemowe

- Własne linie socket/connect/sendto/recvfrom lub read/write z trace:
- Powiązanie z krokami HTTP; ewentualny EINPROGRESS:

### 5. Nasłuch, PID, /proc i adres bind

- Wiersz ss -tlnp, PID własnego serwera, socket inode i link w /proc:
- Różnica między 127.0.0.1 a 0.0.0.0:

## Dokumentacja i zakończenie

- Wynik man -t ps | ps2pdf - ... albo brakujące narzędzie:
- Zatrzymane własne procesy; zapisane pliki dowodowe:
