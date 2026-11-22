# Orkiestrator: działanie, złożoność i poprawność

## Cel i oznaczenia

Wejście A zawiera n nieujemnych liczb całkowitych; k ≥ 1 oznacza liczbę grup.
Celem jest minimalizacja rozstępu D = max(Sⱼ) − min(Sⱼ), gdzie Sⱼ to suma grupy.
B oznacza wydzielony zbiór większych liczb, m = |B|, a R pozostałe wystąpienia.
Dopuszczamy puste grupy.
Orkiestrator jest rozwiązaniem heurystycznym: znajduje poprawny podział,
ale nie gwarantuje minimalnego rozstępu dla całego wejścia.

## CV i wybór ścieżki

**CV = s/x̄** opisuje zróżnicowanie danych względem średniej [1].
W kodzie x̄ jest średnią, a s odchyleniem standardowym.
Domyślny próg τ = 0,6 jest parametrem projektu.

## Przebieg algorytmu

1. **Oblicz CV.** Jeśli CV ≤ τ, zwróć podział całego A uzyskany przez KK.
2. **Wydziel większe liczby.** Dla CV > τ utwórz B z wystąpień aᵢ ≥ x̄ + s;
   pozostałe wystąpienia umieść w R.
3. **Podziel B przez LP.** Zastosuj model LP ze startem
   KK/GNP, ograniczeniem rozstępu, granicami sum i nierosnącym porządkiem sum.
   Wszystkie te wartości oblicz wyłącznie dla B. Pusty B nie uruchamia solvera.
4. **Obsłuż błąd LP.** Jeśli wynik jest błędny lub solver nie zwróci rozwiązania
   dopuszczalnego, zapisz przyczynę i zastosuj KK do B.
5. **Dopełnij grupy przez GNP.** Przetwarzaj R malejąco, każdą liczbę dokładając
   do grupy o aktualnie najmniejszej sumie.
6. **Zweryfikuj wynik.** Sprawdź, czy powstało k grup i zachowano wszystkie
   wystąpienia liczb, łącznie z duplikatami.


## Złożoność obliczeniowa

Poniższa analiza jest **analitycznym oszacowaniem kosztu obecnej implementacji**,.


- **Statystyki i podział:** obliczenie średniej, odchylenia, CV oraz wydzielenie
  B i R wymagają O(n) operacji.
- **GNP dla r elementów:** sortowanie kosztuje O(r log(r+1)), budowa kopca O(k),
  a przypisania O(r log(k+1)). Łącznie
  **G(r,k) = O(r log(r+1) + r log(k+1) + k)**.
- **KK dla r elementów:** kopiec wymaga O(r log(r+1)), a sortowanie k grup przy
  scalaniu O(rk log(k+1)). Kopiowanie list elementów może kosztować do O(r²).
  Stąd zachowawcza granica **K(r,k) = O(r² + rk log(k+1) + r log(r+1) + k)**.
- **LP dla B:** start KK/GNP kosztuje K(m,k) + G(m,k). Budowa modelu i przypisania
  startowego kosztuje O(mk+k); model ma mk zmiennych binarnych i O(m+k) ograniczeń.
  Czas samego solvera oznaczamy T_solve. Przestrzeń przypisań ma kᵐ elementów,
  lecz kᵐ nie jest dokładnym kosztem HiGHS: pruning ogranicza przeszukiwanie.
- **Dopełnienie i kontrola:** GNP dla R kosztuje G(n−m,k), a walidacja zachowania
  danych przez sortowanie O(n log(n+1) + k).

Ścieżka bez podziału kosztuje **O(n) + K(n,k)**. Dla ścieżki hybrydowej otrzymujemy
oszacowanie sumaryczne:

**O(n log(n+1) + mk + k) + K(m,k) + G(m,k) + G(n−m,k) + T_solve.**



## Bibliografia

[1] George F. Reed, Freyja Lynn, Bruce D. Meade (2002).
*Use of Coefficient of Variation in Assessing Variability of Quantitative Assays*.
Clinical and Diagnostic Laboratory Immunology, 9(6), 1235–1239.
[Pełny tekst](https://pmc.ncbi.nlm.nih.gov/articles/PMC130103/) ·
[DOI](https://doi.org/10.1128/CDLI.9.6.1235-1239.2002).
