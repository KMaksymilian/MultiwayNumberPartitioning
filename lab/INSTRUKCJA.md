# Instrukcja uruchomienia programu na Windows

Program rozwiązuje trudniejszy wariant zadania, czyli podział liczb na `k` podzbiorów.

## Uruchomienie


```powershell
.\MultiwayNumberPartitioning.exe --lab --algorithm orchestrator --dataset .\TAiOlab.txt -k 5 --cv-threshold 0.55
```

| Parametr | Wartość dla przykładu |
| --- | --- |
| Algorytm | `orchestrator \| gnp  \| kk \| lp` |
| Dane wejściowe | `TAiOlab.txt`|
| Liczba podzbiorów w każdym zbiorze | `k = 5` |
| Domyślny próg CV orkiestratora | `0.55` |
| Plik wynikowy | Obok pliku wejściowego |

Ponowne poprawne uruchomienie zastępuje poprzedni plik wynikowy. Nazwa wyjścia powstaje automatycznie, np. `dane.txt` → `dane_output.txt`.

## Format wyniku

Nagłówek `2 5` oznacza dwa zbiory i pięć podzbiorów na zbiór. Po nagłówku i pomiędzy blokami znajduje się pusty wiersz. Każdy blok zawiera:

1. Sumę zbioru i jego liczby w kolejności z wejścia.
2. Dokładnie `k` wierszy zawierających sumę podzbioru i jego elementy malejąco. Wiersze są uporządkowane malejąco. Pusty podzbiór zajmuje wiersz zawierający `0`.
3. Rozstęp, czyli największą sumę podzbioru pomniejszoną o najmniejszą.

Orkiestrator dobiera metodę na podstawie zmienności danych. Przy małej zmienności stosuje KK, a przy większej dzieli duże liczby z użyciem modelu MILP i przydziela pozostałe zachłannie.


Próg `0.6` jest domyślną konfiguracją programu. Dla zbiorów w `TAiOlab.txt` zmierzone CV wynosi około `0.621` i `0.570`, więc pierwszy uruchamia ścieżkę hybrydową, a drugi KK.





