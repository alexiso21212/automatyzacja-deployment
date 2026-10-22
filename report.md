# Sprawozdanie – Automatyzacja deploymentu aplikacji webowej

## 1. Cel ćwiczenia

Celem ćwiczenia było zaprojektowanie i przygotowanie przykładowego zautomatyzowanego procesu wdrażania aplikacji webowej. Zakres obejmował przygotowanie aplikacji, uruchomienie jej w kontenerach Docker, integrację z bazą danych PostgreSQL, opracowanie testów automatycznych oraz konfigurację procesu CI/CD z wykorzystaniem GitHub Actions. Dodatkowo przygotowano przykładowe manifesty Kubernetes.

## 2. Wykorzystane technologie

- **Python i Flask** – implementacja API aplikacji webowej.
- **PostgreSQL** – relacyjna baza danych przechowująca notatki.
- **Docker** – budowanie obrazu aplikacji w izolowanym środowisku.
- **Docker Compose** – wspólne uruchamianie aplikacji i bazy danych oraz definiowanie zależności między usługami.
- **pytest** – wykonywanie testów automatycznych.
- **Git i GitHub** – kontrola wersji kodu źródłowego.
- **GitHub Actions** – automatyzacja testów, budowania obrazu i opcjonalnego wdrożenia na serwer testowy.
- **Kubernetes** – opcjonalna konfiguracja Deployment, Service, ConfigMap i trwałego wolumenu dla bazy danych.

## 3. Przygotowanie aplikacji

Zaimplementowano aplikację Flask udostępniającą następujące endpointy:

- `GET /` – zwraca podstawowe informacje o aplikacji i dostępnych endpointach.
- `GET /health` – sprawdza dostępność bazy danych i zwraca status kontroli zdrowia.
- `GET /api/notes` – pobiera zapisane notatki.
- `POST /api/notes` – dodaje nową notatkę po sprawdzeniu poprawności danych wejściowych.

Dane przechowywane są w tabeli `notes` w bazie PostgreSQL. Walidacja odrzuca pustą treść oraz notatki dłuższe niż 500 znaków. Parametry połączenia z bazą przekazywane są przez zmienną środowiskową `DATABASE_URL`, dzięki czemu konfiguracja może różnić się w środowisku lokalnym, testowym i kontenerowym.

## 4. Konteneryzacja z użyciem Docker i Docker Compose

W pliku `Dockerfile` opisano budowanie obrazu aplikacji na bazie obrazu Python. Zainstalowano wymagane biblioteki, skopiowano kod aplikacji oraz skonfigurowano uruchamianie serwera Gunicorn. Proces kontenerowy działa jako nieuprzywilejowany użytkownik.

W pliku `docker-compose.yml` zdefiniowano dwie usługi: `web` oraz `db`. Usługa `web` uruchamia aplikację, natomiast `db` korzysta z obrazu PostgreSQL. Usługa aplikacji zależy od poprawnego przejścia kontroli zdrowia bazy danych. Dane bazy są przechowywane w wolumenie `postgres_data`, dzięki czemu nie znikają po zwykłym zatrzymaniu kontenerów.

Uruchomienie środowiska odbywa się poleceniem `docker compose up -d --build`. Poprawność działania można sprawdzić, otwierając `http://localhost:5000/` oraz `http://localhost:5000/health`, a także wykonując żądania do API.

## 5. Testy automatyczne

Przygotowano testy sprawdzające odpowiedź strony głównej, status endpointu zdrowia, możliwość utworzenia i odczytu notatki oraz odrzucanie niepoprawnych danych. Testy korzystają z testowej bazy PostgreSQL. Uruchamia się je poleceniem `pytest -v` po zainstalowaniu zależności z pliku `requirements-dev.txt` i skonfigurowaniu zmiennej `DATABASE_URL`.

Wyniki rzeczywistego uruchomienia testów należy wpisać na podstawie otrzymanego rezultatu. Pozytywny wynik powinien potwierdzić, że podstawowe funkcje API i walidacja działają prawidłowo.

## 6. Automatyzacja CI/CD

Workflow GitHub Actions umieszczono w pliku `.github/workflows/ci-cd.yml`. Dla pushy do gałęzi `main` oraz pull requestów kierowanych do tej gałęzi pipeline uruchamia środowisko PostgreSQL, instaluje zależności Pythona, wykonuje testy i buduje obraz Dockera.

Wdrożenie na serwer testowy jest oddzielnym etapem zależnym od powodzenia testów i budowania obrazu. Jest uruchamiane po ustawieniu zmiennej repozytorium `DEPLOY_ENABLED=true`, dzięki czemu pipeline może działać również bez skonfigurowanego serwera. Dodano również opcjonalny etap powiadomienia o wyniku pipeline przez Slack Incoming Webhook; aktywuje się po dodaniu sekretu `SLACK_WEBHOOK_URL`. Uruchamia się tylko po pushu do `main`. Po skonfigurowaniu sekretów SSH workflow łączy się z serwerem, pobiera zmiany z repozytorium i wykonuje `docker compose up -d --build`. W razie skonfigurowania sekretu Slack wynik testów i wdrożenia jest przesyłany do wskazanego kanału. Rozdzielenie testowania od wdrożenia ogranicza ryzyko publikowania wersji, która nie przechodzi testów.

## 7. Kubernetes – rozszerzenie opcjonalne

Przygotowano manifesty obejmujące ConfigMap, Deployment i Service aplikacji oraz Deployment, Service i PersistentVolumeClaim bazy PostgreSQL. Konfiguracja aplikacji korzysta z kontroli gotowości i kontroli żywotności. Liczbę replik aplikacji ustawiono na dwie, co demonstruje uruchamianie wielu instancji.

Manifesty są przykładową konfiguracją edukacyjną. Przed wdrożeniem należy zbudować obraz i udostępnić go klastrowi, utworzyć sekret z danymi bazy oraz dostosować ustawienia trwałego przechowywania danych do klastra. Dokumentacja zawiera także komendy do sprawdzenia statusu wdrożenia, aktualizacji obrazu i wycofania wersji.

## 8. Weryfikacja i obserwacje

Weryfikacja projektu obejmuje uruchomienie usług przez Docker Compose, sprawdzenie endpointu `/health`, wykonanie operacji dodania i odczytu notatki oraz uruchomienie testów automatycznych. Działanie CI/CD należy potwierdzić na karcie **Actions** w repozytorium GitHub. Automatyczne wdrożenie zadziała dopiero po skonfigurowaniu serwera i sekretów SSH.

**Wyniki do uzupełnienia po uruchomieniu:**

- Docker Compose: `[działa / nie działa]`
- Endpoint `/health`: `[kod HTTP i wynik]`
- Testy pytest: `[liczba zaliczonych / niezaliczonych testów]`
- GitHub Actions: `[sukces / błąd; etap]`
- Wdrożenie na serwer testowy: `[wykonano / nie konfigurowano]`
- Kubernetes: `[wykonano / pominięto jako opcjonalne]`

## 9. Wnioski

Ćwiczenie pokazuje, w jaki sposób połączyć konteneryzację aplikacji z automatyczną weryfikacją kodu i wdrażaniem nowej wersji. Docker ujednolica środowisko uruchomieniowe, a Docker Compose upraszcza koordynację aplikacji i bazy danych. Testy automatyczne pomagają wykrywać regresje przed wdrożeniem, natomiast GitHub Actions ogranicza liczbę ręcznych czynności potrzebnych do sprawdzenia i opublikowania zmian. Kubernetes stanowi możliwe rozszerzenie rozwiązania o wielokrotne repliki, kontrolę stanu i aktualizacje kroczące.
