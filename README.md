# GPS Simulator — Docker

Docker-оточення для підготовки та запуску `gps-sdr-sim`, перевірки файлів і генерації офлайн-IQ-даних. За потреби проєкт також підтримує діагностику HackRF Pro та перевірку прийому UBX-повідомлень на приймачі u-blox ZED-F9P.

Контейнер містить Python 3, Git, GCC, Make, `usbutils`, утиліти HackRF та Python-пакети `pyubx2` і `pyserial`.

> [!CAUTION]
> **RF-передача вимкнена за замовчуванням.** Звичайний запуск працює лише в програмному режимі. Команда `COMMAND_2` (`hackrf_transfer`) зберігається в `src/config.py`, але виконується лише за явного зазначення прапорця `--rf`.
>
> RF-випробування можуть проводитися виключно в належно екранованому, контрольованому та авторизованому середовищі. Не використовуйте обладнання для передачі сигналів у відкритому ефірі або для впливу на роботу сторонніх GNSS-приймачів.

---

## Зміст

- [Можливості](#можливості)
- [Структура проєкту](#структура-проєкту)
- [Вимоги](#вимоги)
- [Підготовка](#підготовка)
- [Збірка Docker-образу](#збірка-docker-образу)
- [Запуск](#запуск)
  - [Програмні перевірки](#1-програмні-перевірки--режим-за-замовчуванням)
  - [Генерація офлайн-IQ](#2-генерація-офлайн-iq)
  - [Перевірка Docker Compose](#3-перевірка-конфігурації-docker-compose)
  - [Апаратна діагностика без RF](#4-апаратна-діагностика-без-rf)
  - [RF-тест із ZED-F9P](#5-rf-тест-із-zed-f9p)
- [Налаштування тестової локації](#налаштування-тестової-локації)
- [Режими та CLI-параметри](#режими-та-cli-параметри)
- [USB passthrough](#usb-passthrough)
  - [Linux](#linux)
  - [Windows + Docker Desktop + WSL 2](#windows--docker-desktop--wsl-2)
- [Автоматизація у Windows](#автоматизація-у-windows)
- [Архітектура `src/`](#архітектура-src)
- [Усунення типових проблем](#усунення-типових-проблем)
- [Залежності](#залежності)

---

## Можливості

- Підготовка та автоматичне клонування репозиторію `gps-sdr-sim`.
- Перевірка структури проєкту, навігаційного файлу та результатів збірки.
- Збірка `gps-sdr-sim` за допомогою GCC і Make.
- Генерація локального файлу `gpssim.bin` з офлайн-IQ-даними.
- Перевірка наявності HackRF у режимі апаратної діагностики.
- Опціональний RF-тест із читанням UBX-повідомлень від u-blox ZED-F9P.
- Запуск у Docker на Windows (через WSL 2) та Linux.

## Структура проєкту

```text
gps-simulator/
├── main.py                  # точка входу
├── README.md
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
├── requirements.txt         # pyubx2, pyserial (для --rf)
├── start-gps-sim.bat        # Windows-обгортка: usbipd + Docker Compose
├── brdc3160.26n             # навігаційний файл, надається користувачем
├── src/
│   ├── __init__.py
│   ├── config.py            # константи, LOCATIONS, COMMAND_1/2
│   ├── shell.py             # run_command / run_directory_command
│   ├── gps_sdr.py           # перевірки, збірка, генерація IQ
│   ├── hackrf.py            # перевірки HackRF (lsusb, hackrf_info)
│   ├── checks.py            # оркестрація перевірок
│   ├── rf_probe.py          # RF-передача та читання UBX із ZED-F9P
│   ├── monitor.py           # моніторинг IQ без RF
│   └── cli.py               # argparse та main()
└── gps-sdr-sim/             # автоматично клонується; зберігається на хості
    ├── gpssim.c
    ├── Makefile
    └── ...
```

У `src/config.py` базовий шлях визначається через:

```python
BASE_DIR = Path(__file__).resolve().parent.parent
```

Каталог проєкту монтується в контейнер як `/workspace`. Завдяки bind mount клонований `gps-sdr-sim/`, навігаційний файл і згенерований `gpssim.bin` залишаються на хості після завершення контейнера.

## Вимоги

### Windows

- Git.
- Docker Desktop із увімкненим WSL 2 backend.
- Запущений Docker Desktop (стан **Running**).
- `usbipd-win` — лише для апаратного/RF-режиму.

Для звичайного програмного режиму не потрібно окремо встановлювати Python, GCC, Make або дистрибутив Ubuntu: необхідні інструменти працюють усередині Linux-контейнера.

### Linux

- Git.
- Docker Engine.
- Docker Compose plugin.
- Права користувача на запуск Docker (або використання `sudo`).
- Для апаратного/RF-режиму — udev-правила для HackRF. Пакет `hackrf` у відповідному дистрибутиві може містити `/etc/udev/rules.d/52-hackrf.rules`; також може знадобитися група `plugdev`.

Python, GCC, Make та інші інструменти проєкту встановлюються всередині Docker-образу.

## Підготовка

Клонуйте репозиторій і перейдіть до каталогу проєкту:

```bash
git clone <URL_ВАШОГО_РЕПОЗИТОРІЮ>
cd gps-simulator
```

Покладіть навігаційний файл у корінь проєкту. Його ім'я має відповідати значенню `BRDC_NAV_FILE` у `src/config.py`. За замовчуванням використовується:

```text
brdc3160.26n
```

Навігаційний файл не входить до репозиторію — користувач має надати власний актуальний файл (наприклад, отриманий із NASA CDDIS або IGS).

## Збірка Docker-образу

З кореня проєкту виконайте:

```bash
docker compose build
```

## Запуск

### 1. Програмні перевірки — режим за замовчуванням

```bash
docker compose run --rm gps-simulator
```

У цьому режимі програма:

1. Перевіряє директорію проєкту.
2. Клонує `gps-sdr-sim`, якщо каталогу ще немає.
3. Перевіряє репозиторій і збирає його за допомогою GCC/Make.
4. Копіює та перевіряє навігаційний файл.
5. Перевіряє вихідні файли й робочу директорію.
6. Не шукає HackRF і не потребує USB-доступу.
7. Не запускає моніторинг і не виконує RF-передачу.

Це рекомендований варіант для першого запуску та перевірки середовища.

### 2. Генерація офлайн-IQ

```bash
docker compose run --rm gps-simulator --mode software --generate
```

Генерація використовує `COMMAND_1` і створює файл:

```text
gps-sdr-sim/gpssim.bin
```

Це локальна генерація файлу: команда не звертається до HackRF і сама по собі не передає RF-сигнал.

Після генерації без `--detached` запускається `run_monitor_loop()`. Він лише відстежує розмір `gpssim.bin` і не передає RF-сигнал.

Щоб завершити роботу після перевірок і генерації, використовуйте `--detached`:

```bash
docker compose run --rm gps-simulator --mode software --generate --detached
```

### 3. Перевірка конфігурації Docker Compose

```bash
docker compose config
```

Команда виводить підсумкову конфігурацію Compose після обробки файлів і змінних.

### 4. Апаратна діагностика без RF

```bash
docker compose --profile hardware run --rm gps-simulator-hardware --mode hardware
```

Сервіс `gps-simulator-hardware` пробросує `/dev/bus/usb` у контейнер і дозволяє доступ до USB major 189 через `device_cgroup_rules`.

Перед запуском потрібно налаштувати USB passthrough на хості (див. розділ [USB passthrough](#usb-passthrough)).

Цей режим виконує програмні перевірки, а також перевірки `lsusb` і `hackrf_info`. Сам по собі він не запускає RF-передачу.

### 5. RF-тест із ZED-F9P

> [!WARNING]
> Використовуйте цей сценарій лише в належно екранованому, контрольованому та авторизованому RF-середовищі. Прапорець `--rf` явно вмикає код, який запускає `hackrf_transfer`.

Команда:

```bash
docker compose --profile hardware run --rm gps-simulator-hardware \
  --mode hardware --generate --rf --detached
```

Послідовність роботи:

1. Виконуються перевірки режиму `hardware`.
2. `COMMAND_1` генерує `gpssim.bin`.
3. `rf_probe.run_rf_probe()` запускає `hackrf_transfer` у фоновому режимі.
4. Паралельно `pyubx2` читає `UBX-NAV-SAT` і `UBX-NAV-STATUS` із ZED-F9P через `/dev/ttyACM0`. Порт і baud rate задаються параметрами `run_rf_probe()`.
5. Скрипт виводить `numSV` і `spoofDetState`.
6. Якщо `numSV > 0` або `spoofDetState` належить до `{2, 3}`, це вважається ознакою того, що приймач бачить сигнал, навіть якщо антиспуфінг блокує виведення координат.
7. `hackrf_transfer` коректно зупиняється.

**Доступ до ZED-F9P:** приймач має бути видимий контейнеру. У Windows його потрібно пробросити в WSL 2 через `usbipd-win` (так само, як HackRF), а в `docker-compose.yml` — розкоментувати `devices: /dev/ttyACM0`. У Linux потрібно підключити пристрій до хоста та додати відповідний `devices: /dev/ttyACM0` у конфігурацію Compose.

## Налаштування тестової локації

У `src/config.py` змініть `ACTIVE_LOCATION`:

```python
ACTIVE_LOCATION = "paris"  # hangzhou, paris, uae
```

Доступні локації:

| Ключ | Місце | Широта | Довгота | Висота |
|---|---|---:|---:|---:|
| `hangzhou` | Hangzhou, China | 30.286502 | 120.032669 | 100 м |
| `paris` | Paris, France | 48.856600 | 2.352200 | 35 м |
| `uae` | Dubai, UAE | 25.204800 | 55.270800 | 16 м |

Тривалість задається параметром `SECONDS_TO_RUN` у секундах. Типове значення — `360`.

## Режими та CLI-параметри

`main.py` підтримує два режими та три додаткові прапорці:

| Параметр | Призначення |
|---|---|
| `--mode software` | Стандартний програмний режим без доступу до апаратури. |
| `--mode hardware` | Програмні перевірки, а також `lsusb` і `hackrf_info` усередині контейнера. |
| `--generate` | Генерує `gpssim.bin` після успішних перевірок. |
| `--rf` | Запускає `hackrf_transfer` і перевірку прийому на ZED-F9P. Потребує `--mode hardware` та наявного `gpssim.bin`. |
| `--detached` | Не запускає `run_monitor_loop()`; завершує роботу після перевірок і генерації. |

Апаратний режим не підключає пристрій до контейнера автоматично. Стандартний `docker-compose.yml` навмисно не надає контейнеру USB-доступу та не використовує `privileged`.

## USB passthrough

### Linux

Docker на Linux може отримати доступ до USB-пристрою через `devices: /dev/bus/usb` і відповідні права доступу.

Точне налаштування залежить від дистрибутива, udev, Docker та конкретного USB-пристрою. Не додавайте `privileged: true` без необхідності: цей параметр надає контейнеру значно ширші привілеї.

### Windows + Docker Desktop + WSL 2

USB-пристрій спочатку потрібно зробити доступним у WSL 2 через `usbipd-win`. Docker Desktop не гарантує автоматичний passthrough HackRF без попереднього налаштування.

Скорочена послідовність (деталі залежать від версії `usbipd-win`):

1. Відкрийте PowerShell від імені адміністратора та знайдіть BUSID:

   ```powershell
   usbipd list
   ```

2. Прив'яжіть пристрій (зазвичай це одноразова операція, яка зберігається після перезавантаження):

   ```powershell
   usbipd bind --busid <BUSID>
   ```

3. Підключіть пристрій до WSL із автоматичним перепідключенням:

   ```powershell
   usbipd attach --wsl --auto-attach --busid <BUSID>
   ```

Після цього апаратний сервіс Docker Compose зможе побачити пристрій, якщо USB-доступ правильно налаштований у WSL і Compose.

## Автоматизація у Windows

У корені проєкту є `start-gps-sim.bat`. Скрипт автоматизує підготовку USB passthrough і запуск апаратного сценарію:

1. Запитує права адміністратора.
2. Шукає HackRF за VID:PID `1d50:6089` через `usbipd list`.
3. Виконує `usbipd bind` і `usbipd attach --wsl --auto-attach`.
4. Перевіряє видимість пристрою у WSL за допомогою `lsusb`.
5. Запускає Docker Compose із профілем `hardware` та параметрами `--mode hardware --generate --rf --detached`.

Перед запуском перевірте:

- `usbipd-win` встановлено. За потреби його можна встановити командою:

  ```powershell
  winget install --interactive --exact dorssel.usbipd-win
  ```

- У `start-gps-sim.bat` значення `WSL_DISTRO` відповідає назві вашого дистрибутива. Перевірити назви можна командою `wsl -l -v`.
- Файл `brdc3160.26n` розташований у корені проєкту.

> **Увага:** `start-gps-sim.bat` запускає сценарій із `--rf`. Запускайте його лише за умов, описаних у попередженні про RF-безпеку.

## Архітектура `src/`

| Модуль | Відповідальність |
|---|---|
| `config.py` | Константи, `LOCATIONS`, `COMMAND_1`, `COMMAND_2`. |
| `shell.py` | Виконання команд через `run_command()` і `run_directory_command()`. |
| `gps_sdr.py` | `check_project_paths()`, `check_repository()`, `build_repository()`, `prepare_navigation_file()`, `check_gps_sdr_files()`, `check_gpssim_bin()`, `run_directory_diagnostics()`, `generate_offline_data()`. |
| `hackrf.py` | Перевірка HackRF через `check_hackrf()` і `check_hackrf_info()`. |
| `checks.py` | `run_checks(mode)` — послідовність перевірок і підсумковий звіт. |
| `rf_probe.py` | `run_rf_probe()` — запуск `hackrf_transfer` у фоновому режимі та читання UBX із ZED-F9P. |
| `monitor.py` | `run_monitor_loop()` — моніторинг `gpssim.bin` без RF-передачі. |
| `cli.py` | Розбір аргументів через `parse_args()` і запуск `main()`. |

`COMMAND_2` збережена в конфігурації для сумісності з наявним кодом. Її викликає лише `rf_probe.run_rf_probe()` і тільки за явного прапорця `--rf`.

## Усунення типових проблем

| Проблема | Що перевірити |
|---|---|
| `Navigation file not found` | Покладіть `brdc3160.26n` у корінь проєкту або змініть `BRDC_NAV_FILE` на фактичне ім'я файлу. |
| `Git clone failed` | Перевірте доступ контейнера до GitHub. |
| Помилка `make` | Перегляньте лог збірки, перевірте актуальність upstream `Makefile` і наявність `build-essential` (а не лише `gcc`). |
| `pip3: not found` | Переконайтеся, що Dockerfile встановлює `python3-pip` і виконує встановлення пакетів через `pip3`. |
| HackRF не знайдено в hardware-режимі | Перевірте USB passthrough до WSL/Docker і права доступу. На програмний режим це не впливає. |
| `[RF][ERROR] pyubx2 / pyserial not installed` | Перевірте `requirements.txt` і встановлення залежностей у Dockerfile. |
| `[RF][ERROR] Cannot open /dev/ttyACM0` | Перевірте USB passthrough для ZED-F9P і наявність `devices: /dev/ttyACM0` у `docker-compose.yml`. |
| `LIBUSB_ERROR_ACCESS` | Перевірте, чи застосовані udev-правила для HackRF на хості та чи має користувач потрібні права. |
| Зміни або файли не зберігаються | Переконайтеся, що запуск відбувається через Compose із bind mount `./:/workspace`. |

## Залежності

`requirements.txt` містить лише:

- `pyubx2`
- `pyserial`

Ці пакети потрібні виключно для `--rf`, щоб читати UBX-повідомлення із ZED-F9P. Решта Python-коду використовує стандартну бібліотеку.

Системні пакети (Python, Git, GCC, Make, утиліти HackRF тощо) встановлюються через `apt` у `Dockerfile`.

---

## Примітки щодо змін у README

Документацію оновлено відповідно до поточної структури проєкту та описаних можливостей:

- Оновлено назву навігаційного файлу на `brdc3160.26n`.
- Описано пакетну структуру `src/` замість монолітного `main.py`.
- Додано інструкцію щодо `start-gps-sim.bat`.
- Документовано параметри `--rf` і `--detached`.
- Додано опис `rf_probe.py` та взаємодії із ZED-F9P.
- Описано USB passthrough і `device_cgroup_rules`.
- Уточнено призначення `pyubx2` і `pyserial`.
