class VideoIsProcessing(Exception):
    def __init__(self):
        self.msg = "The video is still processing on spankbang's servers!"


class VideoUnavailable(Exception):
    def __init__(self, msg):
        self.msg = msg