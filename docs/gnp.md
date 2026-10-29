# Algorytm zachłanny (Greedy Number Partitioning)

## 1. Ogólny opis

Algorytm zachłanny (ang. *Greedy Number Partitioning*, GNP, w wersji z sortowaniem znany też jako LPT – *Longest Processing Time first*) jest algorytmem aproksymacyjnym dla problemu podziału liczb. Dany jest zbiór liczb naturalnych $S = \{a_1, \dots, a_n\}$ oraz liczba $k \ge 1$. Szukamy podziału $S$ na $k$ podzbiorów, których sumy są możliwie zbliżone.

Problem ten jest NP-trudny, więc nie znamy algorytmu wielomianowego, który zawsze daje rozwiązanie optymalne. Algorytm Karmarkara–Karpa działa w czasie wielomianowym i zwraca rozwiązanie, które może być nieoptymalne. Jego błąd jest jednak ograniczony z góry, co wykażemy w sekcji 4.

Idea algorytmu jest prosta: rozpatrujemy liczby od największej do najmniejszej i każdą wkładamy do tej grupy, która w danej chwili ma najmniejszą sumę.

## 2. Pojęcia i kroki algorytmu
### 2.1. Pojęcia

- **Grupa** – lista liczb ze zbioru $S$. Każda z $k$ grup jest jednym z docelowych podzbiorów.
- **Wartość grupy** $w(G)$ – suma liczb w grupie $G$ powiększona o jej sumę początkową.
- **Sumy początkowe** $s_1, \dots, s_k$ – wartości, od których startują grupy. W podstawowym wariancie problemu wszystkie są równe $0$.
- **Najmniejsza / największa grupa** – grupa o najmniejszej / największej **wartości** $w(G)$ (nie liczności).

### 2.2. Kroki algorytmu
**Inicjalizacja.**
1. Utwórz $k$ pustych grup $G_1, \dots, G_k$.
2. Zbuduj kopiec typu min z par $(s_i, i)$, czyli wartości grup razem z ich indeksami.

**Pętla główna.** Dla każdej liczby $x$ z $S$, w kolejności **nierosnącej**:
1. Zdejmij z kopca parę $(w, i)$ o najmniejszej wartości. Przy remisie wybierana jest
   grupa o mniejszym indeksie.
2. Dopisz $x$ do grupy $G_i$.
3. Włóż do kopca parę $(w + x, i)$, czyli zaktualizowaną wartość grupy.

**Wynik.**
Po przetworzeniu wszystkich liczb grupy $G_1, \dots, G_k$ są docelowymi podzbiorami. To, że tworzą poprawny podział, wykazujemy w sekcji 3.

### 2.3. Przykład
$S = \{8, 7, 6, 5, 4\}$, $k = 2$, sumy początkowe $s_1 = s_2 = 0$.

| Liczba | Wybrana grupa | $G_1$ | $G_2$ | Wartości |
|---|---|---|---|---|
| start | – | $[\,]$ | $[\,]$ | $0,\ 0$ |
| 8 | $G_1$ (remis, mniejszy indeks) | $[8]$ | $[\,]$ | $8,\ 0$ |
| 7 | $G_2$ | $[8]$ | $[7]$ | $8,\ 7$ |
| 6 | $G_2$ | $[8]$ | $[7, 6]$ | $8,\ 13$ |
| 5 | $G_1$ | $[8, 5]$ | $[7, 6]$ | $13,\ 13$ |
| 4 | $G_1$ (remis, mniejszy indeks) | $[8, 5, 4]$ | $[7, 6]$ | $17,\ 13$ |

Wynik to sumy $17$ i $13$. Optymalny podział $\{8,7\}, \{6,5,4\}$ ma sumy równe $15$, więc algorytm nie zawsze znajduje optimum. Dla porównania algorytm Karmarkara–Karpa na tych samych danych daje sumy $16$ i $14$.

## 3. Dowód poprawności
Algorytm jest aproksymacyjny, więc nie dowodzimy optymalności wyniku. Dowód poprawności składa się z trzech części:
1. algorytm się zatrzymuje (sekcja 3.1),
2. zwraca poprawny podział zbioru $S$ na $k$ podzbiorów (sekcja 3.2),
3. wynik jest gorszy od optimum co najwyżej o ograniczoną wartość (sekcja 4).

### 3.1. Własność stopu
Pętla główna przechodzi raz po posortowanej liście $n$ liczb, a każda iteracja wykonuje stałą liczbę operacji na kopcu. Algorytm wykonuje dokładnie $n$ iteracji i zawsze się zatrzymuje.

### 3.2. Poprawność wyniku
**Niezmiennik.** Przed każdą iteracją:
- (a) każda już przetworzona liczba należy do dokładnie jednej grupy, a liczby nieprzetworzone nie należą do żadnej,
- (b) kopiec zawiera dokładnie $k$ par, po jednej dla każdej grupy, i dla każdej grupy $G_i$ para ma postać $(w(G_i), i)$.

---
- *Inicjalizacja:* grupy są puste, a kopiec zawiera pary $(s_i, i)$ dla $i = 1, \dots, k$. Niezmiennik zachodzi.
- *Zachowanie:* iteracja zdejmuje z kopca parę $(w, i)$, dopisuje $x$ tylko do $G_i$ i wkłada do kopca parę $(w + x, i)$. Liczba $x$ trafia do dokładnie jednej grupy, inne grupy się nie zmieniają, a para grupy $G_i$     zostaje zastąpiona parą z jej nową wartością. Niezmiennik jest zachowany.

**Zakończenie:** po $n$ iteracjach wszystkie liczby są przetworzone. Z części (a) każda z nich należy do dokładnie jednej grupy, więc grupy $G_1, \dots, G_k$ są parami rozłączne, a ich suma daje $S$. Jest to poprawny podział $S$ na $k$ podzbiorów. Gdy $n < k$, część podzbiorów jest pusta, co jest dopuszczalne. Część (b) niezmiennika gwarantuje ponadto, że w każdej iteracji zdejmowana jest grupa o rzeczywiście najmniejszej wartości. Z tego korzystamy w sekcji 4.

## 4. Jakość rozwiązania
W tej sekcji zakładamy, że wszystkie sumy początkowe są równe $0$, tak jak w podstawowym wariancie problemu.

### 4.1. Lemat: rozpiętość nie przekracza największej liczby
Wprowadźmy oznaczenia:
- $a_{\max} = \max_i a_i$ – największa liczba w $S$,
- **rozpiętość** – różnica między największą i najmniejszą wartością grupy w danej chwili.

**Lemat.** Po każdej iteracji rozpiętość wynosi co najwyżej $a_{\max}$.

*Dowód.* Indukcja po iteracjach. Na początku wszystkie wartości są równe $0$,
więc rozpiętość wynosi $0$.

Rozważmy iterację, w której dokładamy liczbę $x$. Niech przed nią najmniejsza wartość grupy wynosi $l_{\min}$, a największa $l_{\max}$, przy czym z założenia indukcyjnego $l_{\max} - l_{\min} \le a_{\max}$. Liczba $x$ trafia do grupy o wartości $l_{\min}$ (sekcja 3.2), więc:
- nowa największa wartość to $\max(l_{\max},\ l_{\min} + x)$,
- nowa najmniejsza wartość jest nie mniejsza niż $l_{\min}$, bo wartości grup
  mogą tylko rosnąć.

Zatem nowa rozpiętość wynosi co najwyżej
$$\max(l_{\max},\ l_{\min} + x) - l_{\min} = \max(l_{\max} - l_{\min},\ x) \le a_{\max}. \qquad$$

### 4.2. Wniosek: ograniczenie rozpiętości wyniku
Wprowadźmy oznaczenia:
- $M$ – największa wartość grupy w wyniku algorytmu,
- $m$ – najmniejsza wartość grupy w wyniku algorytmu.

Z lematu zastosowanego do ostatniej iteracji:
$$M - m \le a_{\max}.$$

### 4.3. Twierdzenie: gwarancja jakości
Wprowadźmy jeszcze:
- $\Sigma = \sum_{i=1}^{n} a_i$ – suma wszystkich liczb,
- $OPT$ – wartość optymalnego rozwiązania. Dla danego podziału $S$ na $k$ grup patrzymy na grupę o największej sumie; $OPT$ to najmniejsza taka suma, jaką można uzyskać spośród wszystkich możliwych podziałów:
  $$OPT = \min_{(P_1,\dots,P_k)} \ \max_{i} \ \sum_{a \in P_i} a.$$

**Twierdzenie.**
$$M \le \frac{\Sigma}{k} + \frac{k-1}{k}\, a_{\max}.$$

*Dowód.* Z sekcji 4.2 każda z $k$ grup wyniku ma wartość co najmniej $M - a_{\max}$. Jedna grupa ma wartość $M$, a pozostałe $k-1$ grup co najmniej $M - a_{\max}$, więc
$$\Sigma \ge M + (k-1)(M - a_{\max}) = kM - (k-1)\,a_{\max}.$$
Po podzieleniu przez $k$ i przekształceniu otrzymujemy tezę.

Dla optimum zachodzą dwa proste oszacowania:
- $OPT \ge \Sigma / k$, bo największy podzbiór ma sumę nie mniejszą od średniej,
- $OPT \ge a_{\max}$, bo największa liczba musi trafić do któregoś podzbioru.

Podstawiając je do twierdzenia, otrzymujemy:
- **błąd bezwzględny:**
  $$M - OPT \le \frac{k-1}{k}\, a_{\max},$$
- **błąd względny:**
  $$M \le \left(2 - \frac{1}{k}\right) OPT.$$

Zauważmy, że ten dowód nie korzysta z sortowania liczb. Gwarancja $2 - \frac{1}{k}$ zachodzi dla dowolnej kolejności przetwarzania. Sortowanie malejące poprawia gwarancję, co pokazuje sekcja 4.4.

### 4.4. Wyniki z literatury
Dla wersji z sortowaniem malejącym (tak jak w naszej implementacji) udowodniono
dokładniejsze ograniczenie (przytaczamy je bez dowodu - Graham 1969):
$$M \le \left(\frac{4}{3} - \frac{1}{3k}\right) OPT$$

## 5. Złożoność obliczeniowa
### 5.1. Założenia implementacyjne
- Wartości grup trzymamy w kopcu typu min (`heapq`) jako pary `(suma, indeks)`. Wybór najmniejszej grupy to jedno wywołanie `heappop`.
- Grupy  są zwykłymi listami, a liczbę dopisujemy na koniec (`append`).
- Przed pętlą liczby są sortowane malejąco, co tworzy nową listę.

### 5.2. Analiza
| Etap | Koszt |
|---|---|
| Utworzenie $k$ pustych grup | $O(k)$ |
| Budowa kopca (`heapify`) | $O(k)$ |
| Sortowanie $n$ liczb | $O(n \log n)$ |
| Jedna iteracja: `heappop`, `append`, `heappush` | $O(\log k)$ |
| Liczba iteracji (sekcja 3.1) | $n$ |

**Złożoność czasowa:**
$$O\big(k + n \log n + n \log k\big).$$
W typowym przypadku $k \le n$ upraszcza się to do $O(n \log n)$.

**Złożoność pamięciowa:** $O(n + k)$. Posortowana kopia wejścia i grupy zajmują łącznie $O(n)$, a kopiec i lista grup $O(k)$.

## Bibliografia
1. R. L. Graham, *Bounds for certain multiprocessing anomalies*, The Bell System Technical Journal 45(9), 1966, s. 1563–1581, doi:10.1002/j.1538-7305.1966.tb01709.x.
2. R. L. Graham, *Bounds on multiprocessing timing anomalies*, SIAM Journal on Applied Mathematics 17(2), 1969, s. 416–429, doi:10.1137/0117039.
3. *Greedy number partitioning*, Wikipedia, https://en.wikipedia.org/wiki/Greedy_number_partitioning.