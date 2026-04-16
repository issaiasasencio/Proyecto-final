from ultralytics import YOLO

model = YOLO('Modelos/bestn.pt')


model.export(format="mnn")
