import asyncio
from msg_telegram import Messaging

class test_class:

    async def InitRoutine(self):
        print("InitRoutine start")
        count = 0
        while True:
            count += 1
            await asyncio.sleep(5);
            print("InitRoutine" + str(count))
            Messaging.Instance().Send("test_" + str(count))
        
    def __init__(self, upbit, isTest):
        self.Upbit = upbit
        self.is_test = isTest
