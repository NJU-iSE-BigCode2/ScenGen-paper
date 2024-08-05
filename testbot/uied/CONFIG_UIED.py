class Config:

    def __init__(self):
        # Adjustable
        # self.THRESHOLD_PRE_GRADIENT = 4             # dribbble:4 rico:4 web:1
        # self.THRESHOLD_OBJ_MIN_AREA = 55            # bottom line 55 of small circle
        # self.THRESHOLD_BLOCK_GRADIENT = 5

        # *** Frozen ***
        self.THRESHOLD_REC_MIN_EVENNESS = 0.7
        self.THRESHOLD_REC_MAX_DENT_RATIO = 0.25
        self.THRESHOLD_LINE_THICKNESS = 8
        self.THRESHOLD_LINE_MIN_LENGTH = 0.95
        self.THRESHOLD_COMPO_MAX_SCALE = (0.25, 0.98)  # (120/800, 422.5/450) maximum height and width ratio for a atomic compo (button)
        self.THRESHOLD_TEXT_MAX_WORD_GAP = 10
        self.THRESHOLD_TEXT_MAX_HEIGHT = 0.04  # 40/800 maximum height of text
        self.THRESHOLD_TOP_BOTTOM_BAR = (0.045, 0.94)  # (36/800, 752/800) height ratio of top and bottom bar
        self.THRESHOLD_BLOCK_MIN_HEIGHT = 0.03  # 24/800

