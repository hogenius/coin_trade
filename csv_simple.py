import pandas
import os

CONST_FILE = "buy_coin.csv"
CONST_NAME = "Name"
CONST_VALUE = "Value"

def GetIter():
    data = Load()
    for index, row in data.iterrows():
        yield index, row
        # print(row[name])
        # print(row[value])

def Add(name, value = 0):
    
    data = Load()

    # 새로운 데이터를 담은 Series 객체 생성
    new_data = pandas.DataFrame({CONST_NAME:[name], CONST_VALUE:[value]})

    # 데이터 프레임에 추가
    data = pandas.concat([data, new_data], ignore_index=True)

    # CSV 파일 저장
    data.to_csv(CONST_FILE, index=False)

def Load():
    if os.path.exists(CONST_FILE) == False:
        df = pandas.DataFrame(index = None)
        df[CONST_NAME] = []
        df[CONST_VALUE] = []
        df.to_csv(CONST_FILE)
        return df
    else:
        return pandas.read_csv(CONST_FILE)

def Remove():
    os.remove(CONST_FILE)

    
if __name__ == '__main__':

    my_iter_rows = GetIter()
    for index, row in my_iter_rows:
        print(row[CONST_NAME])
        print(row[CONST_VALUE])

    Add("dsadsa",111)

    my_iter_rows = GetIter()
    for index, row in my_iter_rows:
        print(row[CONST_NAME])
        print(row[CONST_VALUE])

    #Remove()

