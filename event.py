from singletone import SingletonInstane

class EventManager(SingletonInstane):
    def __init__(self):
        self.event_handlers = {}

    def Regist(self, event_type, handler):
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)

    def Remove(self, event_type, handler):
        if event_type in self.event_handlers and handler in self.event_handlers[event_type]:
            self.event_handlers[event_type].remove(handler)
    
    def Event(self, event_type, data):
        if event_type in self.event_handlers:
            for handler in self.event_handlers[event_type]:
                handler(data)


if __name__ == '__main__':

    def event_handler1(data):
        print("Event 1 occurred:", data)

    def event_handler2(data):
        print("Event 2 occurred:", data)

    # 이벤트 처리 함수 등록
    EventManager.Instance().Regist("event1", event_handler1)
    EventManager.Instance().Regist("event1", event_handler2)
    EventManager.Instance().Regist("event2", event_handler2)

    # 이벤트 발생
    EventManager.Instance().Event("event1", "Some data")
    EventManager.Instance().Event("event2", "Other data")

    # 이벤트 처리 함수 제거
    EventManager.Instance().Remove("event1", event_handler2)

    # 이벤트 발생
    EventManager.Instance().Event("event1", "Some data")
    EventManager.Instance().Event("event2", "Other data")