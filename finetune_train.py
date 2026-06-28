from ultralytics import YOLO

model = YOLO('/home/bf-robotics/jazzy0605/kassow_RobotUse/models/best20260603.pt')

model.train(
    data         = '/home/bf-robotics/jazzy0605/surgical_instrument_seg.v1i.yolo26/data.yaml',
    epochs       = 50,
    imgsz        = 1280,
    batch        = 4,
    device       = 0,
    optimizer    = 'SGD',
    lr0          = 0.0001,
    lrf          = 0.01,
    momentum     = 0.9,
    weight_decay = 0.0005,
    cos_lr       = True,
    warmup_epochs= 3,
    patience     = 15,
    degrees      = 60,
    fliplr       = 0.5,
    hsv_h        = 0.015,
    hsv_s        = 0.5,
    hsv_v        = 0.4,
    mosaic       = 0.0,
    close_mosaic = 10,
    amp          = True,
    workers      = 8,
    project      = '/home/bf-robotics/jazzy0605/finetune_runs',
    name         = 'yolo11m_finetune_0610',
    exist_ok     = True,
    pretrained   = True,
    verbose      = True,
)
