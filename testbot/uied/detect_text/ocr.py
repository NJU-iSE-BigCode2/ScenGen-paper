import os
import cv2
import numpy as np
from PIL import Image
from paddleocr import PaddleOCR


class OCRDetector:
    def __init__(self):
        self.threshold = 0.8
        self.model_folder = ''
        self.models = {
            'chinese_cht_mobile_v2.0': PaddleOCR(
                lang='chinese_cht',
                det_model_dir=self.model_folder + 'ch_ppocr_mobile_v2.0_det_infer',
                cls_model_dir=self.model_folder + 'ch_ppocr_mobile_v2.0_cls_infer',
                rec_model_dir=self.model_folder + 'chinese_cht_mobile_v2.0_rec_infer',
                use_gpu=False, total_process_num=os.cpu_count(), use_mp=True,
                show_log=False
            ),
            'ch_ppocr_mobile_v2.0_xx': PaddleOCR(
                lang='ch',
                det_model_dir=self.model_folder + 'ch_ppocr_mobile_v2.0_det_infer',
                cls_model_dir=self.model_folder + 'ch_ppocr_mobile_v2.0_cls_infer',
                rec_model_dir=self.model_folder + 'ch_ppocr_mobile_v2.0_rec_infer',
                use_gpu=False, total_process_num=os.cpu_count(), use_mp=True,
                show_log=False
            ),
            'ch_PP-OCRv2_xx': PaddleOCR(
                lang='ch',
                det_model_dir=self.model_folder + 'ch_PP-OCRv2_det_infer',
                cls_model_dir=self.model_folder + 'ch_ppocr_mobile_v2.0_cls_infer',
                rec_model_dir=self.model_folder + 'ch_PP-OCRv2_rec_infer',
                use_gpu=False, total_process_num=os.cpu_count(), use_mp=True, show_log=False),
            'ch_ppocr_server_v2.0_xx': PaddleOCR(
                lang='ch',
                det_model_dir=self.model_folder + 'ch_ppocr_server_v2.0_det_infer',
                cls_model_dir=self.model_folder + 'ch_ppocr_mobile_v2.0_cls_infer',
                rec_model_dir=self.model_folder + 'ch_ppocr_server_v2.0_rec_infer',
                use_gpu=False, total_process_num=os.cpu_count(), use_mp=True,
                show_log=False
            )
        }

    def get_model(self, ocr_model: str):
        return self.models.get(ocr_model, self.models['ch_ppocr_server_v2.0_xx'])

    def apply_model(self, ocr_model: PaddleOCR, img):
        boxes = ocr_model.ocr(np.array(img), cls=False)
        boxes_filtered = []
        for box in boxes[0]:
            pts = box[0]
            if box[1][1] > self.threshold:
                boxes_filtered.append(
                    [int(pts[0][0]), int(pts[0][1]), int(pts[2][0]), int(pts[2][1]), box[1][0]]
                )
        return boxes_filtered

    def detect(self, img):
        model = self.get_model('ch_ppocr_mobile_v2.0_xx')
        img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        return self.apply_model(model, img)
