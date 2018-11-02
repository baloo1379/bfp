# bfp
Baloo Florek Protocol

Cechy:
* połączeniowy,
* wszystkie dane przesyłane w postaci binarnej,
* pole operacji o długości 3 bitów,
* pole statusu o długości 4 bitów,
* pole długości danych o rozmiarze 32 bitów,
* pole danych o zmiennym rozmiarze,
* dodatkowe pola zdefiniowane przez programistę, zagnieżdżane w polu danych.

1. Pole operacji - 3 bitowe pole zawierające informację o jednej z 9 informacji.
    * `000` - dodawanie
    * `001` - odejmowanie
    * `010` - mnożenie
    * `011` - dzielenie
    * `100` - OR
    * `101` - XOR
    * `110` - AND
    * `111` - NOT i silnia (pierwszy argument NOT, drugi silnia)

2. Statusy(Flagi) - 4 bitowe pole zawierające status transmisji.
    * `0000` - rozpoczynanie połączenia (SYN)
    * `0001` - wysyłanie (SEQ)
    * `0010` - odpowiedź (ACK)
    * `0100` - koniec połączenia (FIN)
    * `1000` - 

3. Pole długośći danych - 32 bitowe pole zawierające informacje o długości pola dane.
4. Pole danych, pole w którym znajdują się informacje:
    * pole identyfikatora (SEQ) - 16 bitów
    * pole identyfikatora odpowiedzi (ACK) - 16 bitów
    * pole numeru sesji - 32 bity
    * pole pierwszej liczby - 32 bity
    * pole drugiej liczby - 32 bity