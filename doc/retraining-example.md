# YOLOv8 Hertrainen met Docker voor Objectherkenning

In dit voorbeeld gaan we het YOLOv8-model hertrainen om barcodes (of andere objecten) te detecteren met behulp van de [barcode-detector dataset van Kaggle](https://www.kaggle.com/datasets/kushagrapandya/barcode-detection).
Na de training zetten we het model om naar Hailo’s eigen `.hef`-formaat om het te draaien op de **Raspberry Pi 5 AI Kit**.

---

## Systeemconfiguratie (ontwikkelmachine)

**Hardware**:

* CPU: Intel i7-6850K
* GPU: NVIDIA RTX 4080

**Software**:

* OS: Ubuntu 20.04
* Hailo DFC-versie: 3.27.0
* Hailo Model-Zoo: 2.11.0

---

## Op de ontwikkelmachine

### 1. Installeer Hailo AI Software Suite

Download en installeer de Hailo AI suite via de [Developer Zone](https://hailo.ai/developer-zone/software-downloads/).

Alternatief: installeer de **DFC** en de **Model Zoo** afzonderlijk in dezelfde virtuele omgeving.

### 2. Volg de officiële YOLOv8 retraining-instructies

📎 [YOLOv8 retraining (Hailo Model Zoo)](https://github.com/hailo-ai/hailo_model_zoo/tree/833ae6175c06dbd6c3fc8faeb23659c9efaa2dbe/training/yolov8)

> Let op: we voegen een volume toe met de naam `data` aan de Docker-container.

### 3. Download de dataset

📎 [barcode-detector dataset](https://www.kaggle.com/datasets/kushagrapandya/barcode-detection)

Zorg dat deze dataset:

* in de Docker-container wordt gekopieerd
  **of**
* gemount is via een volume, bijv. `/data`

---

## Start het hertrainen van het model

Op een RTX 4080 duurde het ongeveer 3 uur om 20 epochs te trainen:

```bash
yolo detect train data=/data/barcode-detect/data.yaml model=yolov8s.pt name=retrain_yolov8s epochs=20 batch=8
```

Na de laatste epoch zie je een melding zoals:
📷 `final-epoch.png`

---

## Valideer het nieuw getrainde model

```bash
yolo predict task=detect source=/data/barcode-detect/valid/images/05102009190_jpg.rf.e9661dd52bd50001b08e7a510978560b.jpg model=./runs/detect/retrain_yolov8s/weights/best.pt
```

Verwachte uitvoer:
📷 `validate-model.png`

---

## Exporteer het model naar ONNX

```bash
yolo export model=/workspace/ultralytics/runs/detect/retrain_yolov8s/weights/best.pt imgsz=640 format=onnx opset=11
```

---

## Kopieer het ONNX-model naar buiten de Docker

```bash
cp ./runs/detect/retrain_yolov8s/weights/best.onnx /data/barcode-detection.onnx
```

---

## Sluit de Docker-container af

Gebruik `exit` of `CTRL+D`.

---

## Converteer het model naar Hailo HEF-formaat

Gebruik de Hailo Model Zoo `compile` opdracht. Dit kan tot 30 minuten duren:

```bash
hailomz compile yolov8s \
  --ckpt=barcode-detection.onnx \
  --hw-arch hailo8l \
  --calib-path barcode-detect/test/images/ \
  --classes 2 \
  --performance
```

> Na succesvolle compilatie zie je:
> 📷 `successful-compilation.png`

---

## Model gebruiken op Raspberry Pi 5 AI Kit

Na succesvolle compilatie krijg je een bestand `yolov8s.hef`.
Dit bestand kan gebruikt worden op de Raspberry Pi 5 met de AI Kit of AI HAT.

📎 Zie [Hergetrainde modellen gebruiken](basic-pipelines.md#using-retrained-models) voor instructies voor deployment.

---

## Voorbeeldtoepassingen voor objectherkenning

Wil je het model gebruiken voor andere objecten zoals:

* Productherkenning in een magazijn
* Voertuigdetectie in videobeelden
* Voorraadscanning met camera

... dan hoef je enkel de dataset en het aantal klassen (`--classes`) aan te passen tijdens de training en compilatie.

