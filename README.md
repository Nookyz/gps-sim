
# GPS Simulator — Docker

Docker/Podman-оточення для `gps-sdr-sim`: офлайн-генерація IQ-даних, діагностика HackRF Pro та опціональне RF-тестування з приймачем u-blox ZED-F9P.

> ⚠️ **Передавання RF-сигналу за замовчуванням вимкнене.**  
> `hackrf_transfer` запускається лише за наявності прапорця `--tx` або `--rf`. Використовуйте обладнання виключно в екранованому, контрольованому та авторизованому середовищі. Не передавайте сигнали у відкритий ефір.

> 🧪 **Linux: стан тестування.**  
> Базовий сценарій (режим `software`, генерація IQ-даних) перевірений. Апаратний режим (`--tx` / `--rf`) на «чистій» системі Linux **потребує додаткового тестування**. Для його роботи можуть знадобитися udev-правила для HackRF, відповідні права груп `plugdev` / `dialout`, а також rootful-режим Podman або Docker. Наведена нижче інструкція є початковим варіантом налаштування, а не гарантією працездатності.

## Зміст

- [Швидкий старт (Windows)](#швидкий-старт-windows)
- [Швидкий старт (Linux)](#швидкий-старт-linux)
- [Команди](#команди)
- [Параметри запуску](#параметри-запуску)

## Швидкий старт (Windows)

### 1. Підготовка

- Встановіть [Podman Desktop](https://podman-desktop.io/) або Docker Desktop та переконайтеся, що середовище запущене.
- Встановіть `usbipd-win`:

  ```powershell
  winget install --interactive --exact dorssel.usbipd-win
  ```

- Клонуйте репозиторій.
- Помістіть навігаційний файл `brdc3190.26n` у кореневу директорію проєкту.

### 2. Запуск через `.bat` (рекомендований спосіб)

```powershell
.\start-gps-sim.bat
```

Запуск у режимі TX (HackRF, без ZED-F9P):

```powershell
.\start-gps-sim.bat tx
```

Запуск у режимі RF (HackRF + ZED-F9P):

```powershell
.\start-gps-sim.bat rf
```

Скрипт автоматично:

- запитує права адміністратора, якщо вони необхідні;
- створює обгортку `docker.bat` для `podman`, якщо команда `docker` відсутня;
- збирає Docker-образ, якщо його ще не створено;
- підключає HackRF (а для режиму `rf` також ZED-F9P) через `usbipd`;
- перевіряє доступність USB-пристроїв у WSL;
- запускає `docker compose` з відповідними параметрами.

### 3. Ручний запуск (альтернативний спосіб)

Збірка Docker-образу:

```powershell
docker compose build
```

Запуск у програмному режимі:

```powershell
docker compose run --rm gps-simulator --mode software
```

Запуск апаратного режиму з генерацією IQ та передаванням через HackRF:

```powershell
docker compose --profile hardware run --rm gps-simulator-hardware --mode hardware --generate --tx
```

## Швидкий старт (Linux)

> 🧪 **Увага:** апаратний режим потребує додаткового тестування. Нижче наведено мінімальну інструкцію для початкового налаштування.

### 1. Підготовка

- Встановіть Docker Engine та плагін Docker Compose (rootful-режим).
- Додайте поточного користувача до групи `docker`:

  ```bash
  sudo usermod -aG docker $USER
  newgrp docker
  ```

- Для HackRF створіть файл udev-правил `/etc/udev/rules.d/52-hackrf.rules`:

  ```text
  SUBSYSTEM=="usb", ATTR{idVendor}=="1d50", ATTR{idProduct}=="6089", MODE="0666"
  ```

- Перезавантажте правила udev:

  ```bash
  sudo udevadm control --reload-rules
  sudo udevadm trigger
  ```

- Клонуйте репозиторій.
- Помістіть навігаційний файл `brdc3190.26n` у кореневу директорію проєкту.

### 2. Запуск

Збірка Docker-образу:

```bash
docker compose build
```

Запуск у програмному режимі:

```bash
docker compose run --rm gps-simulator --mode software
```

Генерація IQ-даних із завершенням роботи після генерації:

```bash
docker compose run --rm gps-simulator --mode software --generate --detached
```

Апаратний режим із генерацією IQ та передаванням через HackRF:

```bash
docker compose --profile hardware run --rm gps-simulator-hardware --mode hardware --generate --tx
```

### 3. Особливості використання Podman у rootless-режимі

- `device_cgroup_rules` не підтримуються. Видаліть відповідні параметри з `docker-compose.yml`.
- Додайте `userns_mode: keep-id` до сервісу `gps-simulator`, щоб уникнути помилки `Operation not permitted` під час монтування bind-mount.
- Для роботи з апаратним забезпеченням рекомендується використовувати rootful Podman (`sudo podman`) або Docker Engine.

## Команди

| № | Команда | Опис | HackRF | ZED-F9P |
|---|---|---|---|---|
| 1 | `docker compose run --rm gps-simulator --mode software` | Лише перевірки програмного середовища | Ні | Ні |
| 2 | `docker compose run --rm gps-simulator --mode software --generate --detached` | Перевірки та генерація IQ із завершенням роботи | Ні | Ні |
| 3 | `docker compose run --rm gps-simulator --mode software --generate` | Перевірки, генерація IQ та моніторинг | Ні | Ні |
| 4 | `... --mode hardware --detached` | Перевірки обладнання через `lsusb` / `hackrf_info` | Так | Ні |
| 5 | `... --mode hardware --generate --tx` | Генерація IQ та циклічне передавання через HackRF | Так | Ні |
| 6 | `... --mode hardware --tx` | Передавання через HackRF без повторної генерації IQ | Так | Ні |
| 7 | `... --mode hardware --generate --rf` | Генерація IQ, RF-передавання та читання UBX із ZED-F9P | Так | Так |
| 8 | `... --mode hardware --rf` | RF-передавання та читання UBX без повторної генерації IQ | Так | Так |

## Параметри запуску

| Параметр | Призначення |
|---|---|
| `--mode software` | Програмний режим без доступу до апаратного забезпечення (за замовчуванням) |
| `--mode hardware` | Програмні перевірки, а також діагностика USB-пристроїв через `lsusb` і `hackrf_info` |
| `--generate` | Генерація файлу `gpssim.bin` |
| `--tx` | Циклічне передавання IQ-даних через `hackrf_transfer` (потрібен HackRF) |
| `--rf` | Передавання через `hackrf_transfer` та читання UBX-даних із ZED-F9P (потрібні HackRF і пристрій `/dev/ttyACM0`) |
| `--detached` | Завершення роботи після перевірок та/або генерації IQ без запуску передавання чи моніторингу |