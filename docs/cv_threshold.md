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
Domyślnie jest to 30 wartości CV × 10 zbiorów dla każdego rozkładu, a jedno wywołanie LP może trwać do `time_limit = 1` s. Pełne badanie zajmuje więc kilkanaście minut. Mniejszy przebieg:
```python
from experiments_cv import run_threshold_study, print_threshold_study

study = run_threshold_study(distributions=["lognormal", "gamma"], ks=(3,),
                            cvs=[0.2, 0.4, 0.6, 0.8, 1.0, 1.5, 2.0],
                            n=40, num_datasets=4, time_limit=0.3, seed=0)
print_threshold_study(study)
```

## 6. Wstępne wyniki
Mała próba z punktu 5 (rozkłady lognormal i gamma, $k = 3$, $n = 40$, 4 zbiory na wartość CV, koszt $D/\sum$):

| Scenariusz | $\tau^*$ | 95% CI | regret (test) | $\tau = 0{,}6$ | zawsze KK | zawsze LP+GNP |
|---|---|---|---|---|---|---|
| lognormal | 1,82 | [1,74; 1,82] | 1,7e-05 | 9,7e-04 | 0 | 4,2e-03 |
| gamma | 2,22 | [2,15; 2,22] | 4,5e-06 | 4,4e-04 | ≈0 | 3,2e-03 |

Najlepszy próg wypada na największym zmierzonym CV, czyli w praktyce wybierana jest strategia „zawsze KK”. Ręczne sprawdzenie pojedynczych instancji potwierdza, że LP faktycznie się wykonuje (status `Optimal` lub `TimeLimit`), a mimo to KK daje wyraźnie mniejszy rozstęp:

| $n$ | CV | $D$ (LP+GNP) | $D$ (KK) |
|---|---|---|---|
| 40 | 0,4 | 3262 | 11 |
| 40 | 2,0 | 463 | 17 |
| 100 | 1,0 | 1012 | 4 |
| 100 | 2,0 | 104 | 5 |

LP dzieli duże liczby optymalnie, ale GNP rozkłada pozostałe liczby gorzej niż KK. Przy kryterium samego rozstępu ścieżka LP+GNP nie wygrywa więc w żadnym zbadanym zakresie CV, a próg $0{,}6$ daje regret o 1–2 rzędy wielkości większy niż „zawsze KK”.

Próba była mała, więc wynik wymaga potwierdzenia w pełnym badaniu, z większym $n$, różnymi $k$ i ewentualnie z kosztem uwzględniającym czas ($\lambda > 0$).
