# Raspberry Pi 5 en Hailo instellen (Nederlandse handleiding)

In deze handleiding leer je hoe je de Raspberry Pi 5 instelt met een Hailo-8 of Hailo-8L AI-versneller.

## Inhoudsopgave

* [Wat heb je nodig](#wat-heb-je-nodig)
* [Hardware](#hardware)
* [Software](#software)
* [Probleemoplossing](#probleemoplossing)

---

## Wat heb je nodig

* Raspberry Pi 5 (8GB aanbevolen)
* Raspberry Pi 5 AI KIT (optie 1):

  * Raspberry Pi M.2 M-Key HAT
  * Hailo-8L M.2 M-Key module (Hailo-8 wordt ook ondersteund)
* Raspberry Pi 5 AI HAT (optie 2):

  * 26TOPs en 13TOPs worden ondersteund
* Actieve koeler voor de Raspberry Pi 5
* Optioneel: koelblok
* Optioneel: een officiële Raspberry Pi camera (bijv. Camera Module 3 of High-Quality Camera)
* Optioneel: USB-camera

---

## Hardware

Voor deze handleiding gebruikten we de Raspberry Pi 5 samen met de officiële actieve koeler en een 27W USB-C-voedingsadapter. We raden aan om de officiële voeding te gebruiken om te zorgen dat het bord voldoende stroom heeft voor de M.2 HAT.

### Raspberry Pi M.2 M-Key HAT

De Raspberry Pi M.2 M-Key HAT is te gebruiken met de Hailo-8L M.2 key M of B+M module (Hailo-8 wordt ook ondersteund).
Gebruik de thermische pad tussen de M.2 module en de HAT voor een goede warmtegeleiding. Zorg bij gebruik in een behuizing voor voldoende ventilatie. Voeg eventueel een koelblok toe op de Hailo-8L module.

📎 [Installatiehandleiding AI Kit van Raspberry Pi](https://www.raspberrypi.com/documentation/accessories/ai-kit.html#ai-kit)

### Raspberry Pi AI HAT

De AI HAT is een zelfstandige oplossing die de Hailo-8L AI-versneller al bevat.
Plug-and-play met de Raspberry Pi 5. Zorg ook hier voor goede koeling.

📎 [Handleiding AI HAT van Raspberry Pi](https://www.raspberrypi.com/documentation/accessories/ai-hat-plus.html#ai-hat-plus)

### Raspberry Pi Camera

📎 [Installatiehandleiding Raspberry Pi camera](https://www.raspberrypi.com/documentation/accessories/camera.html#install-a-raspberry-pi-camera)

---

## Software

### Installeer Raspberry Pi OS

Download en installeer de laatste versie van Raspberry Pi Imager via [raspberrypi.com](https://www.raspberrypi.com/software/)

---

### Installeer je AI Kit of AI HAT

* Voor AI Kit: volg de [AI Kit-gids](https://www.raspberrypi.com/documentation/accessories/ai-kit.html#ai-kit)
* Voor AI HAT: volg de [AI HAT-gids](https://www.raspberrypi.com/documentation/accessories/ai-hat-plus.html#ai-hat-plus)

---

### Installeer de Hailo Software

Volg de instructies in de [AI Software gids van Raspberry Pi](https://www.raspberrypi.com/documentation/computers/ai.html#getting-started)

Dit installeert:

* Hailo firmware
* HailoRT runtime (zie [HailoRT GitHub](https://github.com/hailo-ai/hailort))
* Hailo TAPPAS Core (inclusief GStreamer-elementen en post-processing tools)
* `rpicam-apps` Hailo demo's

---

### Zet PCIe op Gen3

Voor optimale prestaties met Hailo moet PCIe op Gen3 worden gezet.

```bash
sudo raspi-config
```

* Kies optie “6 Advanced Options”
* Daarna “A8 PCIe Speed”
* Kies “Yes” om Gen 3 in te schakelen
* Herstart daarna:

```bash
sudo reboot
```

---

### Verifieer installatie

Controleer of het systeem de Hailo-chip herkent:

```bash
hailortcli fw-control identify
```

Verwachte uitvoer:

```
Executing on device: 0000:01:00.0
Identifying board
Control Protocol Version: 2
Firmware Version: 4.17.0
Board Name: Hailo-8
Device Architecture: HAILO8L
Serial Number: N/A
Part Number: N/A
Product Name: N/A
```

💡 N/A bij serienummer, partnummer en productnaam is normaal bij gebruik van de AI HAT.

---

### Test TAPPAS Core installatie

#### GStreamer Hailotools:

```bash
gst-inspect-1.0 hailotools
```

Verwachte uitvoer bevat plugins zoals:

* hailocounter
* hailofilter
* hailoexportzmq
* hailonv12togray
* enz.

#### GStreamer HailoRT inference:

```bash
gst-inspect-1.0 hailo
```

Verwachte plugins:

* hailonet
* synchailonet
* hailodevicestats

Geen output? Probeer:

```bash
rm ~/.cache/gstreamer-1.0/registry.aarch64.bin
```

---

### Ga door met [hailo\_rpi5\_examples](../README.md#configure-environment)

Werk je lokale repository bij:

```bash
cd [jouw-map]/hailo-rpi5-examples
git pull
```

---

## Probleemoplossing

🤝 Vragen? Bezoek het [Hailo Community Forum](https://community.hailo.ai/)

### PCIe Problemen

Controleer met:

```bash
lspci | grep Hailo
```

Verwachte output:

```
0000:01:00.0 Co-processor: Hailo Technologies Ltd. Hailo-8 AI Processor (rev 01)
```

Zo niet:

* Controleer de verbinding
* Gebruik de officiële voeding
* Zorg dat PCIe geactiveerd is in `raspi-config`
* Controleer of de firmware van je Pi up-to-date is

---

### Driverproblemen

Controleer kernelversie:

```bash
uname -a
```

Versie moet **hoger zijn dan 6.6.31**. Zo niet:

```bash
sudo apt update
sudo apt full-upgrade
```

---

## Bekende Problemen

### PCIe pagina-grootte probleem

Foutmelding:

```bash
max_desc_page_size given 16384 is bigger than hw max desc page size 4096
```

Fix:

```bash
echo "options hailo_pci force_desc_page_size=4096" | sudo tee /etc/modprobe.d/hailo_pci.conf
```

Controleer:

```bash
cat /etc/modprobe.d/hailo_pci.conf
```

---

### Fout: Kan geen geheugen toewijzen in static TLS block

Foutmelding:

```bash
Failed to load plugin ... libgomp.so.1: cannot allocate memory in static TLS block
```

Voeg toe aan `.bashrc`:

```bash
echo 'export LD_PRELOAD=/usr/lib/aarch64-linux-gnu/libgomp.so.1' >> ~/.bashrc
```

Als je dit al tegenkwam:

```bash
export LD_PRELOAD=/usr/lib/aarch64-linux-gnu/libgomp.so.1
rm ~/.cache/gstreamer-1.0/registry.aarch64.bin
```
