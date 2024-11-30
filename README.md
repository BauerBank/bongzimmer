# bongzimmer

Skript für e-mail Bondrucker

## Install Dependencies

sudo is importend!

```
sudo pip install escpos==1.9
```

```
sudo pip install Requests==2.29.0
```

## Config.h

1. Kopiere config.py.example und nenne sie config.py
2. lese mit dem <code>lsusb</code> die angeschlossenen usb geräte aus lokalaisere den drucker und tausche die beiden IDs im USB Obejekt aus
3. Suche das richtige printer-profile aus den [docs](https://python-escpos.readthedocs.io/en/latest/printer_profiles/available-profiles.html) und ersetzte damit die beiden hinteren einträge des USB Objekts (z.B.: <code>Usb(0x04b8, 0x0202, timeout=0, profile="TM-T88V")</code>) falls dein Drucker kein Profil hat bearbeite die beiden hinteren Einträge nicht
4. Passe die IMAP einträge an (health url it optional)

## Udev Rules

Damit dasSkript zugriff auf den Drucker hat muss einen udev Ruel erstellt werden.

```
sudo nano /etc/udev/rules.d/99-usbftdi.rules
```

Kopiere Folgende Zeile in die Datei und passe die Vendore ID an

```
SUBSYSTEM=="usb", ATTRS{idVendor}=="04b8", MODE="0666"
```

Füre folgenden Command aus zum neuladen der udev rules

```
sudo udevadm control --reload-rules && sudo udevadm trigger
```

## Systemd

Damit das Skript automatisch startet und im Hintergrund läuft wird ein Systemd service benötigt.

```
sudo nano /etc/systemd/system/bongzimmer.service
```

Kopiere Folgenden hinhalt und passe den pfad zu main.py und den nutzer an.

```
[Unit]
Description=Bongzimmer
After=default.target

[Service]
Type=simple
Environment="SDL_AUDIODRIVER=pulse" 
WorkingDirectory=/home/flurf3/git/bongzimmer/
ExecStart=/usr/bin/python /home/flurf3/git/bongzimmer/main.py
User=flurf3
Restart=always
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
Environment="PULSE_SERVER=unix:/run/user/1000/pulse/native"

[Install]
WantedBy=default.target
```

Starte und enabel den Service

```
sudo systemctl daemon-reload
sudo systemctl enable bongzimmer.service
sudo systemctl start bongzimmer.service
```

## Telegram Bot

Nachrichten an <https://t.me/wbff3_printer_bot> werden ausgedruckt, wenn der Username in ``allowed_telegram_users.txt`` eingetragen ist.

