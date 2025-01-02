class VideoIsProcessing(Exception):
    def __init__(self):
        self.msg = "The video is still processing on spankbang's servers!"