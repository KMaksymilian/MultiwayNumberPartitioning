# Programowanie liniowe całkowitoliczbowe (LP)

## 1. Ogólny opis
Podejście oparte na programowaniu liniowym zapisuje problem podziału liczb jako model matematyczny i przekazuje go do gotowego solvera. Dany jest zbiór liczb naturalnych $S = \{a_1, \dots, a_n\}$ oraz liczba $k \ge 1$. Szukamy podziału $S$ na $k$ podzbiorów, których sumy są możliwie zbliżone.

Mimo skróconej nazwy LP nie jest to zwykły program liniowy. Zmienne przydziału są binarne, więc jest to program całkowitoliczbowy (ang. *Mixed-Integer Linear Programming*, MILP). Implementacja w `src/algorithm_lp.py` buduje model w bibliotece PuLP, a rozwiązuje go solver HiGHS metodą podziału i ograniczeń.

Sam model jest dokładny: jego optimum to podział o najmniejszej rozpiętości. Implementacja przerywa jednak obliczenia po jednej sekundzie, więc w praktyce może zwrócić rozwiązanie nieoptymalne albo nie zwrócić żadnego (sekcja 4.3).

## 2. Pojęcia i kroki algorytmu
### 2.1. Pojęcia
- **Grupa** $P_j$ – jeden z $k$ docelowych podzbiorów.
- **Suma grupy** $w(P_j)$ – suma liczb w grupie $P_j$ (dla grupy pustej $w(P_j) = 0$).
- **Zmienna przydziału** $x_{ij} \in \{0, 1\}$ – równa $1$ dokładnie wtedy, gdy liczba $a_i$ należy do grupy $P_j$.
- **Zmienne pomocnicze** $L, l \ge 0$ – ciągłe zmienne ograniczające sumy grup z góry i z dołu (w kodzie `max_sum` i `min_sum`).
- **Rozpiętość podziału** – różnica między największą i najmniejszą sumą grupy:
  $$\mathrm{rozp}(P) = \max_j w(P_j) - \min_j w(P_j).$$
- **Relaksacja** – ten sam model, w którym warunek $x_{ij} \in \{0, 1\}$ zastępujemy warunkiem $x_{ij} \in [0, 1]$. Jest to zwykły program liniowy, rozwiązywalny w czasie wielomianowym.

### 2.2. Model
$$
\begin{aligned}
\min \quad & L - l \\
\text{przy warunkach} \quad & \sum_{j=1}^{k} x_{ij} = 1 && i = 1, \dots, n, \\
& L \ge \sum_{i=1}^{n} a_i x_{ij} && j = 1, \dots, k, \\
& l \le \sum_{i=1}^{n} a_i x_{ij} && j = 1, \dots, k, \\
& x_{ij} \in \{0, 1\}, \quad L, l \ge 0.
\end{aligned}
$$

Pierwsza rodzina warunków mówi, że każda liczba trafia do dokładnie jednej grupy. Dwie kolejne wiążą $L$ i $l$ z sumami grup. Model ma $nk + 2$ zmiennych i $n + 2k$ warunków.

### 2.3. Kroki algorytmu
**Budowa modelu.**
1. Utwórz $nk$ zmiennych binarnych $x_{ij}$.
2. Dodaj $n$ warunków przydziału liczb do grup.
3. Dla każdej grupy zbuduj wyrażenie liniowe opisujące jej sumę.
4. Utwórz zmienne $L$ i $l$, a następnie dodaj dla każdej grupy warunki ograniczające.
5. Ustaw funkcję celu $L - l$.

**Rozwiązanie.** Uruchom HiGHS z limitem czasu 1 s. Solver opiera się na metodzie podziału i ograniczeń \[1\], której schemat wygląda następująco:
1. Rozwiąż relaksację bieżącego podproblemu. Jej wartość jest dolnym ograniczeniem wszystkich rozwiązań tego podproblemu.
2. Jeśli ograniczenie nie jest lepsze od najlepszego znanego rozwiązania, odrzuć podproblem.
3. Jeśli wszystkie $x_{ij}$ są całkowite, zapamiętaj rozwiązanie, gdy jest lepsze od dotychczasowego.
4. W przeciwnym razie wybierz zmienną ułamkową i podziel podproblem na dwa: z $x_{ij} = 0$ oraz z $x_{ij} = 1$.

Jest to schemat ogólny, a nie dokładny opis implementacji HiGHS. Rzeczywisty solver dodatkowo upraszcza model, stosuje heurystyki i dodaje płaszczyzny tnące.

**Odczyt wyniku.**
1. Jeśli status solvera jest inny niż `Optimal` lub `Not Solved`, zgłoś błąd.
2. Dla każdej zmiennej $x_{ij}$ o wartości większej niż $0{,}5$ dopisz $a_i$ do grupy $P_j$. Porównanie z $0{,}5$ jest potrzebne, bo solver zwraca wartości zmiennoprzecinkowe.
3. Porównaj multizbiór liczb w grupach z wejściem. Jeśli się różnią, zgłoś błąd.

### 2.4. Przykład
$S = \{8, 7, 6, 5, 4\}$, $k = 2$. Model ma $2 \cdot 5 + 2 = 12$ zmiennych i $5 + 2 \cdot 2 = 9$ warunków:

| Warunek | Postać |
|---|---|
| Przydział liczby $a_i$ | $x_{i1} + x_{i2} = 1$, dla $i = 1, \dots, 5$ |
| Górne ograniczenie | $L \ge 8x_{1j} + 7x_{2j} + 6x_{3j} + 5x_{4j} + 4x_{5j}$, dla $j = 1, 2$ |
| Dolne ograniczenie | $l \le 8x_{1j} + 7x_{2j} + 6x_{3j} + 5x_{4j} + 4x_{5j}$, dla $j = 1, 2$ |

Implementacja zwraca podział $\{6, 5, 4\}, \{8, 7\}$ o sumach równych $15$, czyli $L = l = 15$ i wartość funkcji celu $0$. Jest to optimum. Na tych samych danych algorytm Karmarkara–Karpa daje sumy $16$ i $14$, a algorytm zachłanny $17$ i $13$.

## 3. Dowód poprawności
Dowód poprawności składa się z trzech części:
1. algorytm się zatrzymuje (sekcja 3.1),
2. rozwiązania modelu odpowiadają podziałom zbioru $S$ (sekcja 3.2),
3. optimum modelu to podział o najmniejszej rozpiętości (sekcja 3.3).

Sekcje 3.2 i 3.3 dotyczą modelu. Własności wyniku przerwanego przez limit czasu omawiamy w sekcji 4.3.

### 3.1. Własność stopu
Budowa modelu i odczyt wyniku to skończone pętle po $n$ liczbach i $k$ grupach. Drzewo podziału i ograniczeń jest skończone, bo każdy podział ustala wartość jednej z $nk$ zmiennych binarnych. Dodatkowo limit czasu przerywa przeszukiwanie po jednej sekundzie.

### 3.2. Rozwiązania modelu a podziały
**Lemat.** Przypisania $x$ spełniające warunki modelu odpowiadają wzajemnie jednoznacznie podziałom $S$ na $k$ grup, przy czym grupy mogą być puste.

*Dowód.* Niech $x$ spełnia warunki. Ponieważ $x_{ij} \in \{0, 1\}$ oraz $\sum_j x_{ij} = 1$, dla każdego $i$ istnieje dokładnie jedno $j$ takie, że $x_{ij} = 1$. Liczba $a_i$ należy więc do dokładnie jednej grupy. Odwrotnie, każdy podział wyznacza dokładnie jedno takie przypisanie $x$. Dla dowolnego $x$ warunki na $L$ i $l$ można spełnić, np. przyjmując $L = \sum_i a_i$ oraz $l = 0$. Gdy $n < k$, część grup jest pusta, co jest dopuszczalne.

### 3.3. Funkcja celu a rozpiętość
**Twierdzenie.** Wartość optymalna modelu jest równa najmniejszej rozpiętości spośród wszystkich podziałów $S$ na $k$ grup.

*Dowód.* Ustalmy przypisanie $x$ i odpowiadający mu podział $P$. Warunki dają $L \ge \max_j w(P_j)$ oraz $l \le \min_j w(P_j)$, więc
$$L - l \ge \mathrm{rozp}(P).$$
Równość zachodzi dla $L = \max_j w(P_j)$ i $l = \min_j w(P_j)$. Te wartości są dopuszczalne, bo liczby w $S$ są nieujemne. Dla ustalonego $x$ najmniejsza wartość funkcji celu wynosi więc $\mathrm{rozp}(P)$. Minimalizacja po wszystkich $x$ daje, z sekcji 3.2, minimum po wszystkich podziałach.

## 4. Jakość rozwiązania
### 4.1. Rozpiętość a $OPT$
Analizy w `wstęp.md`, `gnp.md` i `kk.md` oceniają wynik względem $OPT$, czyli najmniejszej możliwej sumy największej grupy. Model minimalizuje natomiast rozpiętość, czyli to samo kryterium, które opisuje `README.md` i którym benchmark w `src/testing.py` porównuje algorytmy. Niech $\Sigma = \sum_{i=1}^{n} a_i$.

**Dla $k = 2$ kryteria są równoważne.** Niech $L$ i $l$ oznaczają sumy większej i mniejszej grupy. Dwie grupy zawierają razem wszystkie liczby, więc $L + l = \Sigma$, skąd $l = \Sigma - L$ oraz $L - l = 2L - \Sigma$. Wartość $\Sigma$ zależy tylko od danych wejściowych, a nie od podziału, więc rozpiętość rośnie wraz z $L$. Najmniejsza rozpiętość oznacza zatem najmniejszą sumę większej grupy.

**Dla $k \ge 3$ kryteria mogą się różnić.** Suma $\Sigma - L$ rozkłada się wtedy na co najmniej dwie grupy, więc $\Sigma$ i $L$ nie wyznaczają już $l$. Dla $S = \{8, 8, 8, 11, 13, 17\}$ i $k = 3$:

| Podział | Sumy | Rozpiętość | Największa suma |
|---|---|---|---|
| $\{8, 11\}, \{8, 13\}, \{8, 17\}$ | $19, 21, 25$ | $6$ | $25$ |
| $\{8, 8, 8\}, \{11, 13\}, \{17\}$ | $24, 24, 17$ | $7$ | $24$ |

Pierwszy podział ma najmniejszą rozpiętość, a drugi osiąga $OPT = 24$. Model wybierze pierwszy, więc nawet rozwiązanie optymalne dla modelu nie musi być optymalne w sensie $OPT$.

### 4.2. Gwarancja dla rozwiązania optymalnego modelu
Niech $M$ będzie największą sumą grupy, a $R$ rozpiętością podziału. Każda z pozostałych $k-1$ grup ma sumę co najmniej $M - R$, więc
$$\Sigma \ge M + (k-1)(M - R), \qquad \text{czyli} \qquad M \le \frac{\Sigma}{k} + \frac{k-1}{k}\, R.$$
Z oszacowania $OPT \ge \Sigma / k$ otrzymujemy
$$M - OPT \le \frac{k-1}{k}\, R.$$

Rozwiązanie optymalne modelu ma rozpiętość nie większą niż jakikolwiek inny podział, w tym wynik algorytmu Karmarkara–Karpa, dla którego $R \le a_{\max}$ (`kk.md`, sekcja 4.2). Dla podziału optymalnego w sensie modelu zachodzą więc te same gwarancje co dla tamtego algorytmu:
$$M - OPT \le \frac{k-1}{k}\, a_{\max}, \qquad M \le \left(2 - \frac{1}{k}\right) OPT.$$
W szczególności, gdy $R = 0$, wynik jest równy $OPT$.

### 4.3. Skutki limitu czasu
Gwarancje z sekcji 4.2 obowiązują tylko dla rozwiązania z udowodnioną optymalnością. Po upływie limitu możliwe są dwa przypadki:

| Stan solvera | Status w PuLP | Zachowanie `algorithm_lp` |
|---|---|---|
| Znaleziono rozwiązanie, bez dowodu optymalności | `Optimal` | Zwraca najlepszy znaleziony podział, bez gwarancji jakości. |
| Nie znaleziono rozwiązania | `Not Solved` | Zmienne nie mają wartości, więc kontrola kompletności zgłasza błąd `Solver returned an incomplete partition.` |

Status `Optimal` nie oznacza więc, że wynik jest optymalny. Odróżnia to dopiero atrybut `sol_status` problemu, którego kod nie sprawdza. Na tej podstawie nie da się rozpoznać, czy zwrócony wynik ma gwarancje z sekcji 4.2.

Przerwanie jest częste, bo relaksacja modelu jest słaba. Przypisanie $x_{ij} = 1/k$ daje wszystkim grupom sumę $\Sigma / k$, więc $L = l$ i relaksacja ma wartość $0$ niezależnie od danych. Do tego model nie usuwa symetrii: permutacja grup daje inne przypisanie $x$ o tej samej wartości, więc każdy podział na niepuste grupy występuje w $k!$ wersjach.

W orkiestratorze błędy `algorithm_lp` są przechwytywane, a zamiast niego uruchamiany jest algorytm Karmarkara–Karpa.

## 5. Złożoność obliczeniowa
### 5.1. Założenia implementacyjne
- Model budujemy w PuLP 3.3.2.
- Solver HiGHS wywołujemy przez pakiet `highspy` z limitem `timeLimit=1`.
- Limit obejmuje tylko pracę solvera, a nie budowę modelu w Pythonie.
- Zakładamy $k \ge 1$. Dla $k = 0$ model jest sprzeczny i funkcja zgłasza błąd.

### 5.2. Analiza
| Etap | Koszt |
|---|---|
| Utworzenie $nk + 2$ zmiennych | $O(nk)$ |
| Budowa $n + 2k$ warunków ($3nk + 2k$ niezerowych współczynników) | $O(nk)$ |
| Rozwiązanie bez limitu czasu, pesymistycznie | wykładniczy względem $nk$ |
| Rozwiązanie z limitem czasu | ograniczony przez limit 1 s |
| Odczyt wartości zmiennych | $O(nk)$ |
| Kontrola kompletności (sortowanie) | $O(n \log n)$ |

Możliwych przypisań liczb do grup jest $k^n$, a w najgorszym przypadku solver musi przejrzeć drzewo o rozmiarze wykładniczym, rozwiązując w węzłach relaksacje.

**Złożoność czasowa:** bez limitu wykładnicza. Z limitem wynosi $O(nk + n \log n)$ plus stały czas pracy solvera, ale kosztem utraty gwarancji optymalności.

**Złożoność pamięciowa:** $O(nk)$ na model oraz pamięć solvera na drzewo przeszukiwania.

### 5.3. Pomiary
Pojedyncze uruchomienia na liczbach losowanych jednostajnie z zakresu $1, \dots, 1000$. Rozpiętość algorytmu Karmarkara–Karpa podano dla porównania.

| $n$ | $k$ | Czas | Dowód optymalności | Rozpiętość LP | Rozpiętość KK |
|---|---|---|---|---|---|
| 30 | 3 | 0,44 s | tak | 0 | 2 |
| 100 | 5 | 1,05 s | nie | 2 | 1 |
| 300 | 10 | 1,32 s | nie | 503 | 1 |
| 1000 | 20 | 2,76 s | nie | 1438 | 1 |

Dla małych instancji model daje wynik lepszy od algorytmów aproksymacyjnych. Dla dużych instancji jedna sekunda nie wystarcza i wynik jest wyraźnie gorszy. Czas ponad limit to budowa modelu i odczyt wyniku.

## Bibliografia
1. A. H. Land, A. G. Doig, *An automatic method of solving discrete programming problems*, Econometrica 28(3), 1960, s. 497–520, doi:10.2307/1910129.
2. Q. Huangfu, J. A. J. Hall, *Parallelizing the dual revised simplex method*, Mathematical Programming Computation 10(1), 2018, s. 119–142, doi:10.1007/s12532-017-0130-5.
3. S. Mitchell, M. O'Sullivan, I. Dunning, *PuLP: A Linear Programming Toolkit for Python*, The University of Auckland, 2011.
4. *Multiway number partitioning*, Wikipedia, https://en.wikipedia.org/wiki/Multiway_number_partitioning.
