# Instrukcja uruchomienia programu na Windows

Program rozwiązuje trudniejszy wariant zadania, czyli podział liczb na `k` podzbiorów z możliwie małą różnicą między największą a najmniejszą sumą.

## Uruchomienie dla prowadzącego

Pobierz `MultiwayNumberPartitioning.exe` i `TAiOlab.txt` z tego katalogu. Zapisz je obok siebie w katalogu, w którym masz prawo zapisu. Otwórz PowerShell w tym katalogu i wykonaj:

```powershell
.\MultiwayNumberPartitioning.exe --lab --algorithm orchestrator --dataset .\TAiOlab.txt -k 5 --cv-threshold 0.55
```

| Parametr | Wartość dla przykładu |
| --- | --- |
| Algorytm | `orchestrator` |
| Dane wejściowe | `TAiOlab.txt`, dwa zbiory odtworzone z przykładu w wiadomości prowadzącego |
| Liczba podzbiorów w każdym zbiorze | `k = 5` |
| Próg CV orkiestratora | `0.55` |
| Plik wynikowy | `TAiOlab_output.txt`, obok pliku wejściowego |

Program nie wymaga osobnej instalacji Pythona. Po zakończeniu wyświetla ścieżkę zapisanego pliku. Ponowne poprawne uruchomienie zastępuje poprzedni plik wynikowy. Aby sprawdzić inny zbiór, podaj jego ścieżkę przez `--dataset` i liczbę podzbiorów przez `-k`. Nazwa wyjścia powstaje automatycznie, np. `dane.txt` → `dane_output.txt`.

## Format wyniku

Nagłówek `2 5` oznacza dwa zbiory i pięć podzbiorów na zbiór. Po nagłówku i pomiędzy blokami znajduje się pusty wiersz. Każdy blok zawiera:

1. Sumę zbioru i jego liczby w kolejności z wejścia.
2. Dokładnie `k` wierszy zawierających sumę podzbioru i jego elementy malejąco. Wiersze są uporządkowane malejąco leksykograficznie według list elementów, z pominięciem pola sumy przy porównywaniu. Pusty podzbiór zajmuje wiersz zawierający `0`.
3. Rozstęp, czyli największą sumę podzbioru pomniejszoną o najmniejszą.

Orkiestrator dobiera metodę na podstawie zmienności danych. Przy małej zmienności stosuje KK, a przy większej dzieli duże liczby z użyciem modelu MILP i przydziela pozostałe zachłannie. Końcowy podział może różnić się od podziału w przykładzie prowadzącego.

Próg `0.55` dobrano do demonstracji ścieżki hybrydowej. CV obu zbiorów wynosi około `0.621` i `0.570`, więc w obu przypadkach orkiestrator uruchamia MILP dla dużych liczb, a następnie GNP dla reszty. W trybie laboratoryjnym próg można ustawić od `0` do `1` włącznie. Oczekiwany rozstęp to `1` dla każdego zbioru. Jest optymalny, ponieważ ani `66`, ani `61` nie dzieli się przez `5`, więc rozstęp `0` jest niemożliwy. Dołączony `TAiOlab_output.txt` pochodzi z uruchomienia programu.

## Zbudowanie programu ze źródeł

Wymagane są Windows, Python 3.13 i `uv`. Z katalogu głównego repozytorium uruchom:

```powershell
uv sync --locked --python 3.13
uv pip install --python .\.venv\Scripts\python.exe pyinstaller==6.22.0
& .\.venv\Scripts\python.exe -m PyInstaller --onefile --name MultiwayNumberPartitioning `
    --collect-all pulp --collect-all highspy `
    --copy-metadata pulp --copy-metadata highspy `
    src/main.py
.\dist\MultiwayNumberPartitioning.exe --lab --algorithm orchestrator --dataset .\lab\TAiOlab.txt -k 5 --cv-threshold 0.55
```

Gotowy program powstaje w `dist\MultiwayNumberPartitioning.exe`. Ostatnie polecenie zapisuje `lab\TAiOlab_output.txt`.
