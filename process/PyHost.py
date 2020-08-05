import mmap
from xml.dom.minidom import parse
import xml.dom.minidom
import time
import serial


prefix = "<AIDA64>"
suffix = "</AIDA64>"    #用于完善从AIDA64读取出的数据
dataFlame_set = set()   #建立数据帧集合

#单个数据帧
class dataFlame:
    label = ""
    value = ""

    def __init__(self,label,value):
        self.label = label
        self.value = value

    def __str__(self):
        return ("<" + self.label + "=" + self.value + ">").encode("utf-8")

def Get_AIDA64_SensorValues(): #解析AIDA64共享的内存信息，读取相应的数据
    AIDA64_values = mmap.mmap(-1, 1300, tagname="AIDA64_SensorValues", access=mmap.ACCESS_READ).read() #AIDA64共享的内存映射文件名为AIDA64_SensorValues
    AIDA64_values = bytes.decode(AIDA64_values, "utf-8").strip(b'\x00'.decode()) #将读取的字节流转换为字符串
    return prefix + AIDA64_values + suffix

def ParseXmlInfo(xml_str):
    #将解析出来的xml字符串进行解析，并设置好格式帧
    DOMTree = xml.dom.minidom.parseString(xml_str)
    collection = DOMTree.documentElement
    dataFlame_set.clear() #清除上一次发送的数据帧

    # sys temp fan
    sys = collection.getElementsByTagName("sys") #获取对应不同的子节点
    temp = collection.getElementsByTagName("temp")
    fan = collection.getElementsByTagName("fan")

    # id label value
    #print("----SysInfo----")
    for info in sys:
        id = info.getElementsByTagName("id")[0].childNodes[0].data
        label = info.getElementsByTagName("label")[0].childNodes[0].data
        value = info.getElementsByTagName("value")[0].childNodes[0].data

        flame = dataFlame(label,value)
        dataFlame_set.add(flame)

        # print(id + "\t" + label + "\t" + value)

    #print("----TempInfo----")
    for info in temp:
        id = info.getElementsByTagName("id")[0].childNodes[0].data
        label = info.getElementsByTagName("label")[0].childNodes[0].data
        value = info.getElementsByTagName("value")[0].childNodes[0].data
        if(id == "TCPU"):
            flame = dataFlame("CPU Temperature", value)
        else:
            flame = dataFlame(label, value)
        dataFlame_set.add(flame)

        # print(id + "\t" + label + "\t" + value)

    #print("----FanInfo----")
    for info in fan:
        id = info.getElementsByTagName("id")[0].childNodes[0].data
        label = info.getElementsByTagName("label")[0].childNodes[0].data
        value = info.getElementsByTagName("value")[0].childNodes[0].data
        if(id == "FCPU"):
            flame = dataFlame("CPU FAN", value)
        elif(id == "FGPU1"):
            flame = dataFlame("GPU FAN", value)
        else:
            flame = dataFlame(label, value)
        dataFlame_set.add(flame)

        # print(id + "\t" + label + "\t" + value)

    return dataFlame_set

def send_com(dataFlame_set,protx,bps): #向串口发送数据 protx为对应的串口号，bps为波特率，波特率应设置与下位机启动串口通讯时启动的波特率相同
    try:
        conn_serial = serial.Serial(protx,bps,timeout=5)
        for dataFlame in dataFlame_set:
            conn_serial.write(dataFlame.__str__()) #向串口写入数据
        conn_serial.close() #关闭通讯
    except Exception as e:
        print("! send fail !" + e.__str__())

if(__name__ == "__main__"):

    #使用一个死循环，不断地获取内存中的信息并通过串口向下位机发送数据
    while(True):
        try:
            AIDA64_values = Get_AIDA64_SensorValues()
            result_set = ParseXmlInfo(AIDA64_values)
            send_com(result_set,"COM3",1500000)
            time.sleep(1) #暂停1秒
        except :
            time.sleep(1) #发生异常后进行忽略，暂停1秒后继续运行
            continue






