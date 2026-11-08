# Wybór progu CV orkiestratora

## 1. Problem
Orkiestrator (`src/orchestrator.py`) wybiera ścieżkę na podstawie współczynnika zmienności $\mathrm{CV} = s/\bar{x}$:

- $\mathrm{CV} \le \tau$ – cały zbiór dzieli KK,
- $\mathrm{CV} > \tau$ – duże liczby dzieli LP, a resztę dokłada GNP (ścieżka LP+GNP).

Domyślny próg $\tau = 0{,}6$ został ustawiony arbitralnie. Ten dokument opisuje metodę empirycznego wyboru $\tau$, zaimplementowaną w `src/experiments_cv.py`.

## 2. Kluczowa obserwacja
Próg nie zmienia działania żadnej z gałęzi, decyduje tylko, która z nich zostanie użyta. Wystarczy więc dla każdej instancji $x$ raz obliczyć wynik obu gałęzi:

- $c_{KK}(x)$ – koszt podziału KK (to samo co `cv_threshold = inf`),
- $c_{LP}(x)$ – koszt ścieżki LP+GNP, wymuszonej przez `cv_threshold = 0`.

Koszt orkiestratora dla dowolnego progu $\tau$ wynosi wtedy
$$
c_\tau(x) =
\begin{cases}
c_{KK}(x) & \text{gdy } \mathrm{CV}(x) \le \tau, \\
c_{LP}(x) & \text{w przeciwnym razie.}
\end{cases}
$$
Przegląd dowolnej liczby progów nie wymaga ponownego uruchamiania algorytmów.

## 3. Funkcja celu
Surowe $D = \max_j S_j - \min_j S_j$ rośnie razem z CV, więc nie nadaje się do uśredniania po różnych instancjach. Domyślnym kosztem jest rozstęp znormalizowany sumą, $D / \sum_i a_i$ (pole `std_max`). Opcjonalnie można doliczyć czas:
$$
c(x) = \frac{D(x)}{\sum_i a_i} + \lambda \cdot t(x),
$$
gdzie $\lambda$ to parametr `time_weight`.

Progi porównujemy przez średni **regret**, czyli stratę względem wyroczni, która zawsze wybiera lepszą gałąź:
$$
\mathrm{regret}(\tau) = \frac{1}{N} \sum_{x} \Big( c_\tau(x) - \min\big(c_{KK}(x),\, c_{LP}(x)\big) \Big).
$$

## 4. Procedura
1. **Zbieranie danych** (`collect_branch_results`). Dla zadanych wartości CV, rozkładu, $n$ i $k$ generujemy zbiory i uruchamiamy na nich obie gałęzie. Zapisujemy zmierzone CV oraz $D$, $D/\sum$ i czas każdej gałęzi.
2. **Kandydaci na próg** (`candidate_thresholds`). Funkcja regretu zmienia się tylko między kolejnymi zmierzonymi wartościami CV. Wystarczy więc sprawdzić $0$ (zawsze LP+GNP), środki między kolejnymi CV oraz największe CV (zawsze KK).
3. **Krzywa regretu** (`regret_curve`). Po posortowaniu instancji po CV koszt dla każdego progu liczymy z sum prefiksowych w czasie $O(N \log N)$.
4. **Wybór progu** (`best_threshold`). Jeśli minimum osiąga kilka progów, wybieramy środkowy z nich, a nie skrajny, bo lepiej uogólnia się na nowe dane.
5. **Walidacja krzyżowa** (`cross_validate_threshold`). Próg dobieramy na $k-1$ częściach danych i mierzymy jego regret na części odłożonej. Dla porównania liczymy też regret progu $0{,}6$, strategii „zawsze KK” i „zawsze LP+GNP”.
6. **Niepewność** (`bootstrap_threshold`). Losowanie ze zwracaniem daje 95% przedział ufności dla $\tau^*$ i pasmo ufności dla całej krzywej regretu.
7. **Wiele scenariuszy** (`minimax_threshold`). Gdy $\tau^*$ różni się między rozkładami lub wartościami $k$, wybieramy próg minimalizujący najgorszy średni regret spośród scenariuszy.

Jeśli optymalny próg wyraźnie zależy od $n$ lub $k$, to samo CV nie wystarcza do wyboru gałęzi. W takim przypadku można zamiast progu dopasować mały klasyfikator (np. płytkie drzewo decyzyjne) na cechach $\mathrm{CV}$, $n$, $k$.

## 5. Uruchomienie
```sh
cd src && uv run python experiments_cv.py
```
Domyślnie jest to 30 wartości CV × 10 zbiorów dla każdego rozkładu, a jedno wywołanie LP może trwać do `time_limit = 1` s. Pełne badanie zajmuje około dziesięć minut:
```python
from experiments_cv import run_threshold_study, print_threshold_study
study = run_threshold_study(ks=(3, 5), n=100, num_datasets=10, time_limit=1, seed=0)
print_threshold_study(study)
```

## 6. Wyniki
Badanie na większych danych: rozkłady lognormal, gamma i uniform, $k \in \{3, 5\}$, $n = 100$, 10 zbiorów na wartość CV, `time_limit = 1` s, koszt $D/\sum$, `seed = 0`:
```python
run_threshold_study(ks=(3, 5), n=100, num_datasets=10, time_limit=1, seed=0)
```

| Scenariusz     | $\tau^*$ | 95% CI       | regret (test) | $\tau = 0{,}6$ | zawsze KK | zawsze LP+GNP |
| -------------- | -------- | ------------ | ------------- | -------------- | --------- | ------------- |
| lognormal, k=3 | 4,50     | [3,93; 4,59] | 3,3e-06       | 2,8e-04        | 3,3e-06   | 7,3e-04       |
| gamma, k=3     | 2,73     | [2,30; 3,86] | 5,0e-07       | 7,5e-05        | 4,8e-07   | 4,7e-04       |
| uniform, k=3   | 0,60     | [0,56; 0,60] | 3,5e-05       | ≈0             | ≈0        | 2,4e-03       |
| lognormal, k=5 | 4,50     | [3,39; 4,59] | 0             | 4,5e-04        | ≈0        | 8,5e-04       |
| gamma, k=5     | 2,67     | [2,41; 2,87] | 2,9e-07       | 9,7e-05        | 2,9e-07   | 3,6e-04       |
| uniform, k=5   | 0,60     | [0,56; 0,60] | 1,2e-05       | ≈0             | ≈0        | 2,7e-04       |
| łącznie        | 4,26     | [3,86; 4,26] | 9,4e-07       | 2,1e-04        | 9,4e-07   | 6,6e-04       |

Próg minimax wynosi $4{,}26$ (najgorszy średni regret $3{,}3 \cdot 10^{-6}$).

- Dla lognormal i gamma $\tau^*$ leży na największym zmierzonym CV lub blisko niego, więc w praktyce wybierana jest strategia „zawsze KK". Próg $0{,}6$ ma regret o 2–3 rzędy wielkości większy, a „zawsze LP+GNP" jest jeszcze gorsza.
- Dla uniform wychodzi $\tau^* = 0{,}6$, ale „zawsze KK" ma regret ≈0. Zakres CV tego rozkładu jest wąski (po 50 zbiorów na scenariusz), więc krzywa regretu jest płaska i wybór progu jest tam mało wiarygodny.
- Różnice między $k = 3$ i $k = 5$ są małe, a przedziały ufności $\tau^*$ się pokrywają. Nie widać wyraźnej zależności progu od $k$.