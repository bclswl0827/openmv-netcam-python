import signal
import serial
import sys
import struct
import time
import json
import argparse
from threading import Thread
from flask import Flask, Response


# 从串口取得图片
def get_snapshot(dev: serial.Serial, keyword: str, data: list[bytes]) -> None:
    while(True):
        try:
            dev.write(keyword.encode())
            size = struct.unpack('<L', dev.read(4))[0]
            data[0] = dev.read(size)
        except:
            return


def send_frames(data: list[bytes]) -> None:  # 合成 mjpeg 流
    while(True):
        time.sleep(0.05)
        yield(b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + data[0] + b'\r\n')


def gracefully_exit(dev: serial.Serial) -> None:  # 优雅退出
    dev.close()
    sys.exit(0)


def read_config(path: str) -> dict:  # 解析配置文件
    with open(path, 'r') as f:
        return json.load(f)


def parse_args() -> dict:  # 解析命令行参数
    parse = argparse.ArgumentParser()
    parse.add_argument('--config', type=str, required=True,
                       help='Path to config file')
    return vars(parse.parse_args())


def register_signal(dev: serial.Serial) -> None:  # 注册信号处理函数
    signal.signal(signal.SIGTERM, lambda signum,
                  frame: gracefully_exit(dev=dev),)
    signal.signal(signal.SIGINT, lambda signum,
                  frame: gracefully_exit(dev=dev),)


# 启动 flask 服务
def start_server(path: str, data: list[bytes], listen: str, port: int) -> None:
    app = Flask(__name__)

    @app.route(path, methods=['GET'])
    def _():
        return Response(
            response=send_frames(data=data),
            mimetype='multipart/x-mixed-replace; boundary=frame',
        )

    app.run(
        host=listen, port=port,
        threaded=True, debug=False,
    )


def main():
    # 读取命令行参数
    cli = parse_args()
    # 读取配置文件
    config = read_config(cli["config"])

    # 打开 OpenMV 串口设备
    serial_dev = serial.Serial(
        dsrdtr=True, rtscts=False,
        xonxoff=False, port=config['device'], timeout=1,
        baudrate=config['baud'], parity=serial.PARITY_NONE,
        bytesize=serial.EIGHTBITS, stopbits=serial.STOPBITS_ONE,
    )
    # 注册信号处理
    register_signal(dev=serial_dev)

    # 从串口取得图片
    data = [b'']
    Thread(target=get_snapshot, args=(
        serial_dev, config['keyword'], data),).start()

    # 启动 flask 服务
    start_server(
        path=config['path'], data=data,
        listen=config['listen'], port=config['port'],
    )


if __name__ == '__main__':
    main()
