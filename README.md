# battlebot_ai

Dit is het AI-gedeelte van het BattleBot-project.

---

## Hailo Hardware en Software Setup op de Raspberry Pi 5

Voor instructies over hoe je Hailo's hardware en software installeert op een Raspberry Pi 5, volg deze handleiding:
[Installatiegids voor Raspberry Pi 5 en Hailo](doc/install-raspberry-pi5.md#how-to-set-up-raspberry-pi-5-and-hailo)

---

## Basic Pipelines

De map `basic_pipelines` bevat standaard pipelines die als uitgangspunt dienen voor verdere ontwikkeling:

* Object Detection (wordt gebruikt in dit project)
* Human Pose Estimation
* Instance Segmentation

Deze pipelines zijn gebaseerd op de [Hailo Apps Infra](https://github.com/hailo-ai/hailo-apps-infra) repository.

---

## Installatie

### 1. Clone de repository

```bash
git clone https://github.com/Matthijs-de-Graaf/battlebot_ai.git
cd battlebot_ai
```

### 2. Voer het installatiescript uit

Dit script automatiseert het downloaden van alle vereiste componenten:

```bash
./install.sh
```

### 3. Activeer de virtuele omgeving

Bij elke nieuwe terminalsessie moet de virtuele omgeving worden geactiveerd:

```bash
source setup_env.sh
```

---

## Documentatie

Meer informatie is beschikbaar in de [Basic Pipelines Documentatie](doc/basic-pipelines.md).

---

## Object Detection

### Eenvoudige versie

Deze lichte versie toont de prestaties van Hailo met minimale belasting van de CPU:

```bash
python basic_pipelines/detection_simple.py
```

Afsluiten met `Ctrl+C`.

![Detection Example](doc/images/detection.gif)

---

### Volledige versie

Deze versie bevat object tracking en ondersteuning voor meerdere videoresoluties:

```bash
python basic_pipelines/detection.py
```

Voor beschikbare opties:

```bash
python basic_pipelines/detection.py --help
```

#### Camera-ingangen

* Raspberry Pi-camera:

  ```bash
  python basic_pipelines/detection.py --input rpi
  ```

* USB-camera (automatisch geselecteerd):

  ```bash
  python basic_pipelines/detection.py --input usb
  ```

* USB-camera met specifiek apparaat:

  ```bash
  get-usb-camera
  python basic_pipelines/detection.py --input /dev/video<X>
  ```

---

## Gebruik van hergetrainde modellen

Deze toepassing ondersteunt ook hergetrainde detectiemodellen. Zie de handleiding:
[Gebruik van hergetrainde modellen](doc/basic-pipelines.md#using-retrained-models)

---

## Pose Estimation

Zie de [documentatie](doc/basic-pipelines.md#pose-estimation-example) voor meer informatie.

```bash
python basic_pipelines/pose_estimation.py
```

Afsluiten met `Ctrl+C`.

![Pose Estimation Example](doc/images/pose_estimation.gif)

---

## Instance Segmentation

Zie de [documentatie](doc/basic-pipelines.md#instance-segmentation-example) voor meer informatie.

```bash
python basic_pipelines/instance_segmentation.py
```

Afsluiten met `Ctrl+C`.

![Instance Segmentation Example](doc/images/instance_segmentation.gif)

---

## Depth Estimation

Zie de [documentatie](doc/basic-pipelines.md#depth-estimation-example) voor meer informatie.

```bash
python basic_pipelines/depth.py
```

Afsluiten met `Ctrl+C`.

![Depth Estimation Example](doc/images/depth.gif)

---

## Raspberry Pi Camera Frameworks

### rpicam-apps

Officiële AI-post-processing voorbeelden van Raspberry Pi met ondersteuning voor de Hailo AI-processor.
Zie de [documentatie](https://www.raspberrypi.com/documentation/computers/ai.html) voor meer informatie.

### picamera2

`picamera2` is de opvolger van de legacy `picamera` en biedt een Python-interface gebaseerd op `libcamera`.
Meer informatie: [Picamera2 GitHub-pagina](https://github.com/raspberrypi/picamera2)

---

## Extra hulpmiddelen

### Hailo Dataflow Compiler (DFC)

De Dataflow Compiler stelt ontwikkelaars in staat om neurale netwerken te compileren voor gebruik met Hailo-8/8L AI-processors.

* Beschikbaar via de [Hailo Developer Zone](https://hailo.ai/developer-zone/software-downloads/) (registratie vereist)
* Voorbeelden en hertraining: [Hailo Model Zoo](https://github.com/hailo-ai/hailo_model_zoo)
* Documentatie en tutorials: [Developer Zone Documentatie](https://hailo.ai/developer-zone/documentation/)

Voor een volledig trainings- en deploymentvoorbeeld, zie:
[Retraining Example](doc/retraining-example.md)
