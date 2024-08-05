import os
from os.path import join as p_join
from typing import Optional

import cv2
import numpy as np

from testbot.uied.detect_compo import ip_region_proposal as ip
from testbot.uied.detect_text import text_detection as text
from testbot.uied.detect_merge import merge as merge


class WidgetDetector:
    def __init__(self):
        self.img: Optional[np.ndarray] = None
        self.img_path: Optional[str] = None
        self.resize_length: int = 800
        self.output_root = ""

        """
            ele:min-grad: gradient threshold to produce binary map         
            ele:ffl-block: fill-flood threshold
            ele:min-ele-area: minimum area for selected elements 
            ele:merge-contained-ele: if True, merge elements contained in others
            text:max-word-inline-gap: words with smaller distance than the gap are counted as a line
            text:max-line-gap: lines with smaller distance than the gap are counted as a paragraph

            Tips:
            1. Larger *min-grad* produces fine-grained binary-map while prone to over-segment element to small pieces
            2. Smaller *min-ele-area* leaves tiny elements while prone to produce noises
            3. If not *merge-contained-ele*, the elements inside others will be recognized, while prone to produce noises
            4. The *max-word-inline-gap* and *max-line-gap* should be dependent on the input image size and resolution

            mobile: {'min-grad':4, 'ffl-block':5, 'min-ele-area':50, 'max-word-inline-gap':6, 'max-line-gap':1}
            web   : {'min-grad':3, 'ffl-block':5, 'min-ele-area':25, 'max-word-inline-gap':4, 'max-line-gap':4}
        """
        self.key_params = {
            "min-grad": 10,
            "ffl-block": 5,
            "min-ele-area": 50,
            "merge-contained-ele": True,
            "merge-line-to-paragraph": True,
            "remove-bar": True,
        }

    def detect(
            self,
            img_path: Optional[str],
            debug: bool = False,
    ):
        if img_path is not None:
            self.img_path = img_path

        if img_path is None or \
                not os.path.exists(img_path):
            raise Exception("No Image for Detection.")

        self.img = cv2.imread(self.img_path)

        self.detect_ocr()
        self.detect_compo()
        img_res_path, resize_ratio, elements = self.detect_merge(debug)
        return img_res_path, resize_ratio, elements["compos"]

    def detect_ocr(self):
        text.text_detection(
            self.img_path,
            self.output_root,
            show=False,
        )

    def detect_compo(self):
        ip.compo_detection(
            self.img_path,
            self.output_root,
            self.key_params,
            resize_by_height=self.resize_length,
            show=False,
        )

    def detect_merge(self, debug: bool = False):
        name = self.img_path.split('/')[-1][:-4]
        compo_path = p_join(self.output_root, 'ip', str(name) + '.json')
        ocr_path = p_join(self.output_root, 'ocr', str(name) + '.json')
        screen_with_bbox_path, elements, resize_ratio = merge.merge(
            self.img_path,
            compo_path,
            ocr_path,
            p_join(self.output_root, "merge"),
            is_remove_bar=self.key_params['remove-bar'],
            is_paragraph=self.key_params['merge-line-to-paragraph'],
            show=debug,
        )
        return screen_with_bbox_path, resize_ratio, elements

    def _resize_height_by_longest_edge(self):
        if self.img is None:
            raise Exception("No Image for Detection.")
        height, width = self.img.shape[:2]
        if height > width:
            return self.resize_length
        else:
            return int(self.resize_length * (height / width))
