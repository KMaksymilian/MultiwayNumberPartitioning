# Przegląd poprawności develop i zakres hotfixa

Podstawa analizy: aktualny `origin/develop`, commit `c668ae1`.
Zmiany przygotowano na osobnej gałęzi `hotfix/develop-correctness`.

## Potwierdzone problemy

| Problem | Odtworzenie i skutek | Poprawka |
|---|---|---|
| Brak importu `get_distribution` w generatorze | `generate_with_target_cv(10, 0.6)` zgłasza `NameError`; eksperymenty nie startują. | Import rejestru rozkładów. |
| Brak importów w diagnostyce generatora | `check_target_cv` i `compare_distributions` zgłaszają `NameError` dla `random` i `DISTRIBUTIONS`; brakowało też funkcji generatora. | Jawne importy potrzebnych zależności. |
| Nieaktualne wywołanie walidatora | `partition_metrics([1,2], [[1],[2]], 2)` zgłasza `TypeError`, bo nie przekazuje `k`. | Przekazanie liczby grup. |
| Niezadeklarowany Matplotlib | Nowy moduł wykresów nie importuje się w środowisku z samymi zależnościami projektu. | Opcjonalny zestaw `plots`, aktualizacja lockfile i CI. |
| Błędne podpisy wskaźnika jakości | Obliczany jest iloraz z przesunięciem o jeden, a podpis podaje iloraz surowy. | Spójne podpisy konsoli i heatmap. |
| Budowanie MILP mimo znalezienia rozstępu zero | Wersja develop z pruningiem nie zawiera skrótu przygotowanego wcześniej na hotfixie. | Powrót przed konstrukcją modelu; po zerowym KK pomijane jest również GNP. |
| Niespójna flaga optimum po błędnym wyniku LP | Odrzucony podział może pozostawić `lp_optimal=True` przy powrocie do KK. | Potwierdzanie flagi dopiero po walidacji; kasowanie jej przy fallbacku. |

Dodatkowo eksperymenty odrzucają niepoprawne rozmiary i parametry, a generator
docelowego CV odrzuca wartości niefinitywne. Nie wprowadzono nowej reguły doboru
algorytmów, nowej funkcji celu ani zmian progu CV.

## Weryfikacja

Nowe testy odtwarzają błędy importów i walidatora, przechodzą przez generowanie
trzech rozkładów, diagnostykę generatora, siatkę parametrów, CV sweep oraz
tworzenie wykresów bez interfejsu graficznego. Sprawdzają również etykiety ilorazu,
pominięcie konstrukcji modelu przy zerze i metadane po odrzuceniu wyniku LP.

```bash
uv run --frozen --extra plots python -m unittest discover -s tests -v
git diff --check
```

## Ograniczenia przeglądu

To przegląd poprawności aktualnych modułów i testów, nie dowód braku wszystkich
błędów. Testy eksperymentów używają małych instancji; nie stanowią pełnego
benchmarku wydajności ani walidacji statystycznej generatorów. Test wykresów
sprawdza tworzenie figur i ich etykiety, nie jakość graficzną całych raportów.
Pełne wyszukiwanie MILP nadal może być kosztowne, a rozwiązanie hybrydowe nie
gwarantuje globalnego optimum.
