"""
  author: dayan
  create_time :  
  description: 
"""
from tushare.subs.ts_subs import Subs


def test_realtime():
    app = Subs()

    #  code 可以包含 * （通配符）
    @app.register(topic='HQ_STK_MIN', codes=["*000001.SZ"])
    def print_message(record):
        """
        订阅主题topic，并指定codes列表，在接收到topic的推送消息时，符合code条件，就会执行回调
        :param record:
        :return:
        """
        print('用户定义业务代码输出 print_message(%s)' % str(record))

    app.run()


if __name__ == '__main__':
    test_realtime()
