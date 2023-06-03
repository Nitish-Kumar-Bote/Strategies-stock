
import time
import json
class inter():
    def __init__(self, symbol1, nuva, streaming_type):
        self.symbol = symbol1
        self.nuva = nuva
        self.streaming_type = streaming_type
        self.list = []

    def callback_(self, resp):
        res1 = json.loads(resp)
        print(res1)
        if self.symbol == 'a9':
            pri = res1['response']['data'].get('a9')
            if pri != None:
                self.list.append(pri)
        elif self.symbol == 'd2':
            pri = res1['response']['data'].get('d2')
            if pri != None:
                self.list.append(pri)

        else:
            self.list.append(res1)

    def stema_data(self):
        quotes_streamer = self.nuva.initQuotesStreaming()
        quotes_streamer.subscribeQuotesFeed(symbols=self.streaming_type, callBack=self.callback_)
        time.sleep(1)
        quotes_streamer.unsubscribeQuotesFeed()

    def __enter__(self):
        self.stema_data()
        return self.list

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass



