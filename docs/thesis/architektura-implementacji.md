# Architektura implementacji

## Organizacja programu

Implementację opracowano w języku Python jako aplikację uruchamianą z wiersza
poleceń. Zastosowano podział modułowy.

## Podział odpowiedzialności

| Moduł | Odpowiedzialność |
|---|---|
| `main.py` | Obsługa parametrów uruchomienia, wybór metody, inicjowanie eksperymentów i eksport wyników do CSV. |
| `orchestrator.py` | Analiza statystyczna danych, wydzielenie podproblemu, koordynacja algorytmów i połączenie ich wyników. |
| `algorithm_kk.py` | Realizacja heurystyki Karmarkara–Karpa z kopcem struktur częściowych podziałów. |
| `algorithm_gnp.py` | Zachłanne rozdzielanie liczb z użyciem kopca aktualnych sum grup. |
| `algorithm_lp.py` | Budowa modelu MILP, przygotowanie rozwiązania początkowego i ograniczeń pruningowych oraz obsługa solvera. |
| `testing.py` | Wczytywanie zestawów, walidacja podziałów, pomiar czasu oraz wyznaczanie i agregacja miar jakości. |
| `dataset_generator.py` | Generowanie i zapisywanie danych testowych z określonym ziarnem losowania. |

## Reprezentacja danych i współpraca modułów

Dane wejściowe są reprezentowane jako lista nieujemnych liczb całkowitych.
Wynik podziału ma postać listy grup, z których każda zawiera przypisane liczby.
Powtarzające się wartości są zachowywane jako osobne wystąpienia, a grupy mogą
pozostać puste.

KK i LP przyjmują zbiór liczb oraz żądaną liczbę grup. Interfejs GNP dodatkowo
uwzględnia sumy istniejących grup i zwraca wyłącznie nowo przypisane elementy.

Moduł LP wykorzystuje bibliotekę PuLP do zapisania funkcji celu, zmiennych
i ograniczeń, a następnie przekazuje model do solvera HiGHS. Rozwiązanie solvera
jest przekształcane do list grup i sprawdzane przed zwróceniem.
