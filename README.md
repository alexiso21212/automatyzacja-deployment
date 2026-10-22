# Automatyzacja deploymentu aplikacji webowej

Projekt demonstracyjny do laboratorium DevOps. Aplikacja Flask zapisuje notatki w PostgreSQL, uruchamiana jest przez Docker Compose, a GitHub Actions automatycznie testuje kod i buduje obraz. Po pushu do gałęzi `main` workflow może również wdrożyć aplikację na skonfigurowany serwer testowy.

## 1. Wymagania

- Docker Desktop / Docker Engine z poleceniem `docker compose`
- Git
- Python 3.12 (potrzebny do uruchamiania testów lokalnie; Docker używa własnego Pythona)
- konto GitHub, jeżeli ma być uruchomione CI/CD

## 2. Uruchomienie aplikacji przez Docker Compose

W katalogu projektu wykonaj:

```bash
docker compose up -d --build
docker compose ps
```

Otwórz `http://localhost:5000/`. Kontrola zdrowia: `http://localhost:5000/health`.

Utworzenie notatki przez API:

```bash
curl -X POST http://localhost:5000/api/notes \
  -H 'Content-Type: application/json' \
  -d '{"content":"Moja pierwsza notatka"}'
```

Odczyt notatek:

```bash
curl http://localhost:5000/api/notes
```

Logi aplikacji i bazy:

```bash
docker compose logs -f web
docker compose logs -f db
```

Zatrzymanie kontenerów (dane bazy w wolumenie pozostają):

```bash
docker compose down
```

Usunięcie kontenerów oraz danych bazy (operacja nieodwracalna dla tego środowiska testowego):

```bash
docker compose down -v
```

## 3. Testy lokalne

Najpierw uruchom samą bazę danych:

```bash
docker compose up -d db
```

Następnie w katalogu projektu utwórz środowisko wirtualne i zainstaluj zależności testowe.

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
export DATABASE_URL='postgresql://appuser:apppassword@localhost:5432/appdb'
pytest -v
```

Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
$env:DATABASE_URL = 'postgresql://appuser:apppassword@localhost:5432/appdb'
pytest -v
```

## 4. Repozytorium GitHub

W GitHub utwórz puste repozytorium, a następnie w katalogu projektu wykonaj (podmień URL na adres własnego repozytorium):

```bash
git init
git add .
git commit -m "Pierwsza wersja aplikacji i pipeline CI/CD"
git branch -M main
git remote add origin https://github.com/TWOJ_LOGIN/automatyzacja-deployment.git
git push -u origin main
```

Workflow znajduje się w `.github/workflows/ci-cd.yml`. Przy każdym pushu do `main` i pull requeście do `main` uruchamia testy oraz buduje obraz Dockera. Job wdrożeniowy uruchamia się wyłącznie po udanym teście i pushu do `main`.

## 5. Automatyczne wdrożenie na serwer testowy

Ta część wymaga własnego serwera Linux z Dockerem, wtyczką `docker compose`, dostępem SSH oraz sklonowanym repozytorium w katalogu `/opt/automatyzacja-deployment`.

Na serwerze wykonaj jednorazowo:

```bash
sudo mkdir -p /opt/automatyzacja-deployment
sudo chown "$USER":"$USER" /opt/automatyzacja-deployment
git clone https://github.com/TWOJ_LOGIN/automatyzacja-deployment.git /opt/automatyzacja-deployment
cd /opt/automatyzacja-deployment
docker compose up -d --build
```

W ustawieniach repozytorium GitHub wybierz **Settings → Secrets and variables → Actions**. W sekcji **Variables** dodaj zmienną `DEPLOY_ENABLED` z wartością `true`, a w sekcji **Secrets** dodaj:

- `SSH_HOST` – adres IP lub domena serwera
- `SSH_USER` – użytkownik SSH
- `SSH_PRIVATE_KEY` – prywatny klucz SSH użytkownika, który ma dostęp do serwera
- `SLACK_WEBHOOK_URL` – opcjonalny adres Incoming Webhook Slacka do powiadomień o wyniku pipeline

Dopóki zmienna `DEPLOY_ENABLED` nie ma wartości `true`, pipeline wykonuje testy i buduje obraz, ale pomija wdrożenie. Workflow zakłada katalog `/opt/automatyzacja-deployment`; w razie potrzeby zmień ścieżkę w `ci-cd.yml`. Klucz publiczny sparowanego klucza SSH musi być zainstalowany na serwerze w `~/.ssh/authorized_keys`. Przed użyciem wdrożenia sprawdź dostęp SSH ręcznie. Nie umieszczaj haseł ani kluczy prywatnych w plikach repozytorium. Powiadomienie Slack jest opcjonalne: bez sekretu `SLACK_WEBHOOK_URL` krok zakończy się pominięciem wysyłki.

Uwaga: przykładowe dane bazy w Compose są przeznaczone wyłącznie do lokalnego laboratorium. Dla serwera użyj silnych wartości i ogranicz ekspozycję portu bazy.

## 6. Kubernetes (opcjonalnie)

Manifesty znajdują się w `k8s/`. Wymagany jest działający klaster oraz obraz aplikacji dostępny dla węzłów klastra. Przykład utworzenia sekretu z danymi do bazy:

```bash
kubectl create secret generic deployment-demo-secret \
  --from-literal=POSTGRES_USER=appuser \
  --from-literal=POSTGRES_PASSWORD='ZMIEŃ_TO_NA_SILNE_HASŁO'
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/postgres.yaml
```

Dla aplikacji zbuduj obraz i udostępnij go klastrowi/rejestrowi. Następnie zmień `image` w `k8s/app.yaml` na właściwą nazwę obrazu i wykonaj:

```bash
kubectl apply -f k8s/app.yaml
kubectl get pods,services
kubectl port-forward service/deployment-demo-service 5000:5000
```

Po przekierowaniu portu otwórz `http://localhost:5000/`. W środowisku produkcyjnym należy dodatkowo ustawić sekrety z bezpiecznego źródła, storage klasy klastra, polityki sieciowe i właściwy rejestr obrazów.

## 7. Przykładowy blue-green / rolling update

Kubernetes Deployment domyślnie wykonuje aktualizację kroczącą (rolling update). Dwa repliki aplikacji i `readinessProbe` pomagają kierować ruch wyłącznie do podów gotowych do obsługi żądań. Po opublikowaniu nowego obrazu można przeprowadzić aktualizację:

```bash
kubectl set image deployment/deployment-demo-app web=NAZWA_REJESTRU/deployment-demo-app:WERSJA
kubectl rollout status deployment/deployment-demo-app
kubectl rollout history deployment/deployment-demo-app
# W razie problemów:
kubectl rollout undo deployment/deployment-demo-app
```

To przykład mechanizmu rolling update. Pełny blue-green wymaga utrzymywania dwóch niezależnych wersji (Blue i Green) i przełączenia selektora Service po walidacji nowej wersji.
