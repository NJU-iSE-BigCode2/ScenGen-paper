from os.path import join as p_join
import os


class Config:

    def __init__(self):
        self.ROOT_IMG_COMPONENT = None
        self.ROOT_MERGE = None
        self.ROOT_OCR = None
        self.ROOT_IP = None
        self.ROOT_IMG_ORG = None
        self.ROOT_INPUT = None
        self.ROOT_OUTPUT = None

    def build_output_folders(self):
        # setting data flow paths
        self.ROOT_INPUT = ""
        self.ROOT_OUTPUT = ""

        self.ROOT_IMG_ORG = p_join(self.ROOT_INPUT, "org")
        self.ROOT_IP = p_join(self.ROOT_OUTPUT, "ip")
        self.ROOT_OCR = p_join(self.ROOT_OUTPUT, "ocr")
        self.ROOT_MERGE = p_join(self.ROOT_OUTPUT, "merge")
        self.ROOT_IMG_COMPONENT = p_join(self.ROOT_OUTPUT, "components")
        if not os.path.exists(self.ROOT_IP):
            os.mkdir(self.ROOT_IP)
        if not os.path.exists(self.ROOT_OCR):
            os.mkdir(self.ROOT_OCR)
        if not os.path.exists(self.ROOT_MERGE):
            os.mkdir(self.ROOT_MERGE)
