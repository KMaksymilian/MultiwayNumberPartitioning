# Instrukcja uruchomienia programu na Windows

Program rozwiązuje trudniejszy wariant zadania, czyli podział liczb na `k` podzbiorów.

## Uruchomienie


```powershell
.\MultiwayNumberPartitioning.exe --lab --algorithm orchestrator --dataset .\TAiOlab.txt -k 5 --cv-threshold 0.6
```

| Parametr | Wartość dla przykładu |
| --- | --- |
| Algorytm | `orchestrator \| gnp  \| kk \| lp` |
| Dane wejściowe | `TAiOlab.txt`|
| Liczba podzbiorów w każdym zbiorze | `k = 5` |
| Domyślny próg CV orkiestratora | `0.6` |
| Plik wynikowy | Obok pliku wejściowego |

Program nie wymaga osobnej instalacji Pythona. Po zakończeniu wyświetla ścieżkę zapisanego pliku. Ponowne poprawne uruchomienie zastępuje poprzedni plik wynikowy. Nazwa wyjścia powstaje automatycznie, np. `dane.txt` → `dane_output.txt`.

## Format wyniku

Nagłówek `2 5` oznacza dwa zbiory i pięć podzbiorów na zbiór. Po nagłówku i pomiędzy blokami znajduje się pusty wiersz. Każdy blok zawiera:

1. Sumę zbioru i jego liczby w kolejności z wejścia.
2. Dokładnie `k` wierszy zawierających sumę podzbioru i jego elementy malejąco. Wiersze są uporządkowane malejąco. Pusty podzbiór zajmuje wiersz zawierający `0`.
3. Rozstęp, czyli największą sumę podzbioru pomniejszoną o najmniejszą.

Orkiestrator dobiera metodę na podstawie zmienności danych. Przy małej zmienności stosuje KK, a przy większej dzieli duże liczby z użyciem modelu MILP i przydziela pozostałe zachłannie.

CV jest ilorazem odchylenia standardowego i średniej, więc może przekraczać `1`. Parametr `--cv-threshold` przyjmuje każdą skończoną wartość nieujemną. Orkiestrator wybiera KK, gdy zmierzone CV nie przekracza progu, a ścieżkę hybrydową przy większym CV.

Próg `0.6` jest domyślną konfiguracją programu. Dla zbiorów w `TAiOlab.txt` zmierzone CV wynosi około `0.621` i `0.570`, więc pierwszy uruchamia ścieżkę hybrydową, a drugi KK.

Wariant z progiem `4.26`, oceniany w raporcie, uruchamia się poleceniem:

```powershell
.\MultiwayNumberPartitioning.exe --lab --algorithm orchestrator --dataset .\TAiOlab.txt -k 5 --cv-threshold 4.26
```

Na tych dwóch przykładach wybiera on KK. W [badaniu porównawczym](../docs/kk_vs_orchestrator.md) na 1420 zbiorach uzyskał wynik równy KK w 1392 przypadkach i gorszy w 28. Dobór progu ma charakter empiryczny i zależy od badanych danych.


