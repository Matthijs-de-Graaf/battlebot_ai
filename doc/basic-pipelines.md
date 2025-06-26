# Hailo RPi5 Basic Pipelines

Deze repository bevat voorbeelden van basispipelines met gebruik van Hailo’s H8 en H8L AI-accelerators. De voorbeelden demonstreren objectdetectie, menselijke pose-estimatie en instance-segmentatie, en bieden een solide basis voor eigen projecten.

Deze repository maakt gebruik van onze [Hailo Apps Infra](https://github.com/hailo-ai/hailo-apps-infra) als afhankelijkheid.
Zie de Development Guide voor meer informatie over hoe je met deze pipelines je eigen toepassingen kunt ontwikkelen.

---

## Installatie

Raadpleeg de [Installatiehandleiding](../README.md#installation) in het hoofd-README-bestand voor gedetailleerde instructies over het instellen van de omgeving.

---

# Overzicht

Deze handleiding geeft een overzicht van hoe je aangepaste toepassingen kunt ontwikkelen met behulp van de basispipelines in deze repository. De voorbeelden tonen objectdetectie, pose-estimatie en instance-segmentatie met gebruik van Hailo’s H8 en H8L accelerators.

---

## Werking van de Callback-methode

Elke pipeline maakt gebruik van een callback-methode om data uit de GStreamer-pipeline te verwerken. Deze methode wordt aangeroepen zodra er nieuwe data beschikbaar is. De functie verwerkt deze data, haalt relevante informatie op en voert gewenste acties uit, zoals het tekenen op videobeelden of het tonen van informatie in de terminal.

### Callbackklasse van de gebruiker

De `user_app_callback_class` is een aangepaste klasse die overerft van `app_callback_class` uit het `hailo_apps_infra`-pakket. Hiermee kun je gebruikersspecifieke gegevens en status beheren over meerdere frames heen. De klasse bevat doorgaans methoden om het aantal verwerkte frames bij te houden, framegegevens te beheren en andere logica toe te passen.

### Belangrijke opmerking over de callbackfunctie

De callbackfunctie is blokkerend. Als deze te lang duurt om uit te voeren, kan de pipeline vastlopen. Voor intensieve verwerking per frame wordt aangeraden om de data naar een apart proces te sturen. Je kan bij hailo-rpi5-examples `WLEDDisplay`-klasse in `community_projects/wled_display/wled_display.py` kijken hoe hun het toevoegen

---

## Beschikbare Pipelines

De voorbeelden in deze repository maken gebruik van het `hailo-apps-infra`-pakket, dat algemene hulpmiddelen en de pipelines zelf levert. Deze pipelines kunnen eenvoudig in eigen toepassingen worden geïmplementeerd.

---

# Objectdetectie Voorbeeld

![Objectdetectie](images/detection.gif)

Dit voorbeeld toont objectdetectie met het YOLOv8s-model (voor Hailo-8L, 13 TOPS) en het YOLOv8m-model (voor Hailo-8, 26 TOPS). Alle modellen die zijn gecompileerd met HailoRT NMS Post Process worden ondersteund.

Alle personen worden gevolgd met een tracking-ID.

### Wat bevat dit voorbeeld?

* **Aangepaste Callbackklasse**: Laat zien hoe je aangepaste variabelen en functies toevoegt voor bijvoorbeeld overlays op frames.
* **Callbackfunctie**: Verwerkt de `HAILO_DETECTION` metadata en haalt label, bounding box, score en tracking-ID op.
* **Extra functies**: Ondersteuning voor aangepaste argumenten met `argparse`, zoals het wijzigen van het model.
* **Hergetrainde modellen**: Gebruik van aangepaste HEF-bestanden en labelbestanden is mogelijk via `--hef-path` en `--labels-json`.

**Voorbeeldgebruik met een aangepast model:**

```bash
python basic_pipelines/detection.py --labels-json resources/barcode-labels.json --hef-path resources/yolov8s-hailo8l-barcode.hef --input resources/barcode.mp4
```

**Voorbeelduitvoer:**
![Barcode Voorbeeld](images/barcode-example.png)

---

# Pose Estimatie Voorbeeld

![Pose Estimatie](images/pose_estimation.gif)

In dit voorbeeld wordt pose-estimatie uitgevoerd met het `yolov8s_pose`-model (voor Hailo-8L) of `yolov8m_pose` (voor Hailo-8).

### Wat bevat dit voorbeeld?

* **Callbackklasse voor Pose Estimatie**: Verwerkt `HAILO_DETECTION` met 17 keypoints (`HAILO_LANDMARKS`).
* **Keypoints Dictionary**: De `get_keypoints()`-functie geeft een mapping van keypointnamen naar indexen (ogen, schouders, heupen, enz.).
* **Frameverwerking**: Bij gebruik van `--use-frame` worden bijvoorbeeld ogen visueel weergegeven op het frame.

---

# Instance Segmentatie Voorbeeld

![Instance Segmentatie](images/instance_segmentation.gif)

Toont hoe maskers van gedetecteerde objecten worden overgelegd op het originele frame.

### Belangrijke kenmerken:

* **Callbackklasse**: Verwerkt `HAILO_DETECTION` met masker (`HAILO_CONF_CLASS_MASK`) metadata.
* **Frames overslaan**: Standaard wordt elke 2e frame verwerkt.
* **Kleurcodering**: Iedere instance krijgt een eigen kleur.
* **Overlay op frame**: Maskers worden geschaald en over het originele frame gelegd.

---

# Diepte-inschatting Voorbeeld

![Diepte-inschatting](images/depth.gif)

Dit voorbeeld toont diepte-inschatting met het `scdepthv3`-model. Hierbij wordt elke pixel voorzien van een extra dimensie: afstand tot de camera.

### Let op

De afstandswaarden zijn vaak relatief, genormaliseerd en niet per definitie meetbaar in meters. Zie het originele [scdepthv3-artikel](https://arxiv.org/abs/2211.03660) voor meer informatie.

### Wat bevat dit voorbeeld?

* **Callbackfunctie**: Verwerkt het `HAILO_DEPTH_MASK` matrix. De callback haalt de matrix op en voert logica uit zoals het berekenen van de gemiddelde diepte (na het verwijderen van de hoogste 5% outliers).
* **Rescaling**: De uitvoer van `scdepthv3` is 320x256, en wordt geschaald naar het originele formaat van de camera.

---

# Aanbevolen werkwijze voor ontwikkeling

* **Begin eenvoudig**: Start met de basisscripts en pas alleen de callbackfunctie aan.
* **Voeg stapsgewijs complexiteit toe**: Breid langzaam uit naar meer geavanceerde pipelines.
* **Pas callbacks aan**: Maak eigen logica in de `app_callback` functie.
* **Raadpleeg de documentatie**: Zie de [TAPPAS Architectuur](https://github.com/hailo-ai/tappas/blob/4341aa360b7f8b9eac9b2d3b26f79fca562b34e4/docs/TAPPAS_architecture.rst) en [Hailo Objects API](https://github.com/hailo-ai/tappas/blob/4341aa360b7f8b9eac9b2d3b26f79fca562b34e4/docs/write_your_own_application/hailo-objects-api.rst#L4) voor diepgaandere kennis.

---

## Debugtips

### Print-statements

Gebruik eenvoudige `print()`-opdrachten om waarden, aantal objecten of coördinaten te inspecteren tijdens het debuggen.

### Debuggen met VS Code

Zie de [gids op het Hailo-communityforum](https://community.hailo.ai/t/debugging-raspberry-pi-python-code-using-vs-code/12595) voor het debuggen op Raspberry Pi via VS Code.

### Haperende video

* Vermijd zware bewerkingen in de callbackfunctie.
* Gebruik de vlag `--disable-callback` om de callback tijdelijk uit te schakelen.
* Gebruik video met lagere resolutie of framerate indien nodig.
* Controleer CPU-belasting met `htop`.
* Monitor Hailo-belasting met:

```bash
export HAILO_MONITOR=1
hailortcli monitor
```

### Pipeline debugging

Zie de [Hailo Apps Infra Developer Guide](https://github.com/hailo-ai/hailo-apps-infra/blob/main/doc/development_guide.md) voor geavanceerde debuginstructies.

---

## Overzicht van scripts

### Omgevingsconfiguratie (vereist bij elke nieuwe terminalsessie)

```bash
source setup_env.sh
```

### Vereisten installeren

```bash
pip install -r requirements.txt
```

Indien nodig:

```bash
sudo apt install -y rapidjson-dev
```

### Download hulpbronnen

```bash
./download_resources.sh
```

Voor alle modellen:

```bash
./download_resources.sh --all
```
