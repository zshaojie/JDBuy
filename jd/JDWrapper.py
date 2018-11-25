# -*- coding: utf-8 -*-

import json
import logging
import pickle

import os
import random
import sys

import bs4
import requests
import time

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(name)s %(levelname)s %(message)s",
                    datefmt='%Y-%m-%d  %H:%M:%S %a'
                    )

# get function name
FuncName = lambda n=0: sys._getframe(n + 1).f_code.co_name


def tags_val(tag, key='', index=0):
    '''
    return html tag list attribute @key @index
    if @key is empty, return tag content
    '''
    if len(tag) == 0 or len(tag) <= index:
        return ''
    elif key:
        txt = tag[index].get(key)
        return txt.strip(' \t\r\n') if txt else ''
    else:
        txt = tag[index].text
        return txt.strip(' \t\r\n') if txt else ''

def tag_val(tag, key=''):
    '''
    return html tag attribute @key
    if @key is empty, return tag content
    '''
    if tag is None:
        return ''
    elif key:
        txt = tag.get(key)
        return txt.strip(' \t\r\n') if txt else ''
    else:
        txt = tag.text
        return txt.strip(' \t\r\n') if txt else ''

class JDWrapper(object):
    '''
    京东抢购封装器，用于登录京东，添加购物车，付款
    '''

    def __init__(self):
        # cookie info
        print u'===================================='
        print u'=        ** 初始化抢购组件 **        ='
        print u'===================================='

        self.trackid = ''
        self.uuid = ''
        self.eid = ''
        self.fp = ''

        # self.usr_name = usr_name
        # self.usr_pwd = usr_pwd

        self.interval = 0

        # init url related
        self.home = 'https://passport.jd.com/new/login.aspx'
        self.login = 'https://passport.jd.com/uc/loginService'
        self.image = 'https://authcode.jd.com/verify/image'
        self.authCode = 'https://passport.jd.com/uc/showAuthCode'

        self.session = requests.Session()

        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36',
            'ContentType': 'text/html; charset=utf-8',
            'Accept-Encoding': 'gzip, deflate, sdch',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Connection': 'keep-alive',
        }

        self.cookies = {

        }

        '''
        try:
            self.browser = webdriver.PhantomJS('phantomjs.exe')
        except Exception, e:
            print 'Phantomjs initialize failed :', e
            exit(1)
        '''

    @staticmethod
    def print_json(resp_text):
        '''
        format the response content
        '''
        if resp_text[0] == '(':
            resp_text = resp_text[1:-1]

        for k, v in json.loads(resp_text).items():
            print u'%s : %s' % (k, v)

    @staticmethod
    def response_status(resp):
        if resp.status_code != requests.codes.OK:
            print 'Status: %u, Url: %s' % (resp.status_code, resp.url)
            return False
        return True

    def check_login(self):
        '''
        检查是否已经登录
        :return: boolean
        '''
        check_url = 'https://passport.jd.com/uc/qrCodeTicketValidation'

        try:
            print '+++++++++++++++++++++++++++++++++++++++++++++++++++++++'
            print u'{0} > 自动登录中... '.format(time.ctime())
            with open('cookie', 'rb') as f:
                cookies = requests.utils.cookiejar_from_dict(pickle.load(f))
                resp = requests.get(check_url, cookies=cookies)

                if resp.status_code != requests.codes.OK:
                    print u'{0} >登录过期， 请重新登录！'
                    return False
                else:
                    return True

            return False
        except Exception as e:
            return False
        else:
            pass
        finally:
            pass

        return False

    def login_by_QR(self):
        '''
        京东二维码登录
        :return:
        '''

        print '+++++++++++++++++++++++++++++++++++++++++++++++++++++++'
        print u'{0} > 请打开京东手机客户端，准备扫码登陆:'.format(time.ctime())

        urls = (
            'https://passport.jd.com/new/login.aspx',
            'https://qr.m.jd.com/show',
            'https://qr.m.jd.com/check',
            'https://passport.jd.com/uc/qrCodeTicketValidation'
        )

        # 【第一步】：打开登录页
        resp = self.session.get(
            urls[0],
            headers=self.headers
        )

        if resp.status_code != requests.codes.OK:
            print u'o(╥﹏╥)o 获取登录页失败: %u' % resp.status_code
            return False

        # 保存cookies
        for k, v in resp.cookies.items():
            self.cookies[k] = v

        # 【第二步】：获取登录二维码
        resp = self.session.get(
            urls[1],
            headers=self.headers,
            cookies=self.cookies,
            params={
                'appid': 133,
                'size': 147,
                't': (long)(time.time() * 1000)
            }
        )

        if resp.status_code != requests.codes.OK:
            print u'o(╥﹏╥)o 获取二维码失败: %u' % resp.status_code
            return False

        # 保存cookies
        for k, v in resp.cookies.items():
            self.cookies[k] = v

        # 保存二维码
        image_file = 'qr.png'
        with open(image_file, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=1024):
                f.write(chunk)

        # 打开文件，扫描二维码
        if os.name == "nt":
            # for windows
            os.system('start ' + image_file)
        else:
            if os.uname()[0] == "Linux":
                # for linux platform
                os.system("eog " + image_file)
            else:
                # for Mac platform
                os.system("open " + image_file)

        # 【第三步】：检查登录状态
        # self.headers['Host'] = 'qr.m.jd.com'
        self.headers['Referer'] = 'https://passport.jd.com/new/login.aspx'

        # check if QR code scanned
        qr_ticket = None
        retry_times = 100
        while retry_times:
            retry_times -= 1
            resp = self.session.get(
                urls[2],
                headers=self.headers,
                cookies=self.cookies,
                params={
                    'callback': 'jQuery%u' % random.randint(100000, 999999),
                    'appid': 133,
                    'token': self.cookies['wlfstk_smdl'],
                    '_': (long)(time.time() * 1000)
                }
            )

            if resp.status_code != requests.codes.OK:
                continue

            n1 = resp.text.find('(')
            n2 = resp.text.find(')')
            rs = json.loads(resp.text[n1 + 1:n2])

            if rs['code'] == 200:
                print u'{} : {}'.format(rs['code'], rs['ticket'])
                qr_ticket = rs['ticket']
                break
            else:
                print u'{} : {}'.format(rs['code'], rs['msg'])
                time.sleep(3)

        if not qr_ticket:
            print u'o(╥﹏╥)o 二维码登陆失败'
            return False

        # 【第四步】：校验登录
        self.headers['Host'] = 'passport.jd.com'
        self.headers['Referer'] = 'https://passport.jd.com/uc/login?ltype=logout'
        resp = self.session.get(
            urls[3],
            headers=self.headers,
            cookies=self.cookies,
            params={'t': qr_ticket},
        )
        if resp.status_code != requests.codes.OK:
            print u'o(╥﹏╥)o 二维码登陆校验失败: %u' % resp.status_code
            return False

        ## 京东有时候会认为当前登录有危险，需要手动验证
        ## url: https://safe.jd.com/dangerousVerify/index.action?username=...
        res = json.loads(resp.text)
        if not resp.headers.get('P3P'):
            if res.has_key('url'):
                print u'需要手动安全验证: {0}'.format(res['url'])
                return False
            else:
                self.print_json(res)
                print u'登陆失败!!'
                return False

        ## login succeed
        self.headers['P3P'] = resp.headers.get('P3P')
        for k, v in resp.cookies.items():
            self.cookies[k] = v

        with open('cookie', 'wb') as f:
            pickle.dump(self.cookies, f)

        print u'登陆成功'
        return True

    def buy(self, options):
        """
        添加购物车，查看购物车，提交付款
        :param options: 商品编码等信息
        :return: 购买结果
        """

        # 查询商品详情
        good_data = self.good_detail(options.good)

        # 如果库存为空，刷新
        if good_data['stock'] != 33:
            # flush stock state
            while good_data['stock'] != 33 and options.flush:
                print u'<%s> <%s>' % (good_data['stockName'], good_data['name'])
                # time.sleep(options.wait / 1000.0)
                good_data['stock'], good_data['stockName'] = self.good_stock(stock_id=options.good,
                                                                             area_id=options.area)

            # retry detail
            # good_data = self.good_detail(options.good)

        link = good_data['link']
        if good_data['stock'] != 33 or link == '':
            # print u'stock {0}, link {1}'.format(good_data['stock'], link)
            return False

        try:
            # 修改购买数量
            if options.count != 1:
                link = link.replace('pcount=1', 'pcount={0}'.format(options.count))

            # 添加购物车
            resp = self.session.get(link, cookies=self.cookies)
            soup = bs4.BeautifulSoup(resp.text, "html.parser")

            # tag if add to cart succeed
            tag = soup.select('h3.ftx-02')
            if tag is None:
                tag = soup.select('div.p-name a')

            if tag is None or len(tag) == 0:
                print u'添加到购物车失败'
                return False

            print ''
            print '+++++++++++++++++++++++++++++++++++++++++++++++++++++++'
            print u'{0} > 添加购物车...'.format(time.ctime())
            print u'{0} > 链接：{1}'.format(time.ctime(), link)
            print u'{0} > 结果：{1}' .format(time.ctime(), tags_val(tag))

        except Exception, e:
            print 'Exp {0} : {1}'.format(FuncName(), e)
        else:
            self.cart_detail()
            return self.order_info(options.submit)

        return False

    def good_detail(self, stock_id, area_id=None):
        """
        查询商品详情
        :param stock_id: 商品编码
        :param area_id: 地区编码
        :return: 商品详情
        """
        print '+++++++++++++++++++++++++++++++++++++++++++++++++++++++'
        print u'{0} > 查询商品详情...'.format(time.ctime())
        # return good detail
        good_data = {
            'id': stock_id,
            'name': '',
            # link：添加购物车连接
            'link': '',
            'price': '',
            'stock': '',
            'stockName': '',
        }

        try:
            # 商品页
            stock_link = 'http://item.jd.com/{0}.html'.format(stock_id)
            resp = self.session.get(stock_link)

            # good page
            soup = bs4.BeautifulSoup(resp.text, "html.parser")

            # good name
            tags = soup.select('div#name h1')
            if len(tags) == 0:
                tags = soup.select('div.sku-name')
            good_data['name'] = tags_val(tags).strip(' \t\r\n')

            # cart link
            tags = soup.select('a#InitCartUrl')
            link = tags_val(tags, key='href')

            if link[:2] == '//': link = 'http:' + link
            good_data['link'] = link
        except Exception, e:
            print 'Exp {0} : {1}'.format(FuncName(), e)

        # good price
        good_data['price'] = self.good_price(stock_id)

        # good stock
        good_data['stock'], good_data['stockName'] = self.good_stock(stock_id=stock_id, area_id=area_id)

        print '--------------------------------------------------------------------------------'
        print '| 商品详情 |'
        print '--------------------------------------------------------------------------------'
        print u'|   编号   | {0}'.format(good_data['id'])
        print u'|   库存   | {0}'.format(good_data['stockName'])
        print u'|   价格   | {0}'.format(good_data['price'])
        print u'|   名称   | {0}'.format(good_data['name'])
        print '--------------------------------------------------------------------------------'
        # print u'链接：{0}'.format(good_data['link'])

        return good_data

    def good_price(self, stock_id):
        '''
        查询商品价格
        :param stock_id: 
        :return: 
        '''
        # get good price
        url = 'http://p.3.cn/prices/mgets'
        payload = {
            'type': 1,
            'pduid': int(time.time() * 1000),
            'skuIds': 'J_' + stock_id,
        }

        price = '?'
        try:
            resp = self.session.get(url, params=payload)
            resp_txt = resp.text.strip()

            js = json.loads(resp_txt[1:-1])
            # print u'价格', 'P: {0}, M: {1}'.format(js['p'], js['m'])
            price = js.get('p')

        except Exception, e:
            print 'Exp {0} : {1}'.format(FuncName(), e)

        return price

    def good_stock(self, stock_id, area_id):
        '''
        查询商品库存
        33 : 有货
        34 : 无货
        '''
        # http://ss.jd.com/ss/areaStockState/mget?app=cart_pc&ch=1&skuNum=3180350,1&area=1,72,2799,0
        #   response: {"3180350":{"a":"34","b":"1","c":"-1"}}
        # stock_url = 'http://ss.jd.com/ss/areaStockState/mget'

        # http://c0.3.cn/stocks?callback=jQuery2289454&type=getstocks&skuIds=3133811&area=1_72_2799_0&_=1490694504044
        #   jQuery2289454({"3133811":{"StockState":33,"freshEdi":null,"skuState":1,"PopType":0,"sidDely":"40","channel":1,"StockStateName":"现货","rid":null,"rfg":0,"ArrivalDate":"","IsPurchase":true,"rn":-1}})
        # jsonp or json both work
        stock_url = 'https://c0.3.cn/stocks'

        payload = {
            'type': 'getstocks',
            'skuIds': str(stock_id),
            'area': area_id or '14_1116_4192_0',  # area change as needed
        }

        try:
            # get stock state
            resp = self.session.get(stock_url, params=payload)
            if not self.response_status(resp):
                print u'获取商品库存失败'
                return (0, '')

            # return json
            resp.encoding = 'gbk'
            stock_info = json.loads(resp.text)
            stock_stat = int(stock_info[stock_id]['StockState'])
            stock_stat_name = stock_info[stock_id]['StockStateName']

            # 33 : on sale, 34 : out of stock, 36: presell
            return stock_stat, stock_stat_name

        except Exception as e:
            print 'Stocks Exception:', e
            time.sleep(5)

        return (0, '')

    def cart_detail(self):
        """
        查询购物车列表
        :return: 购物车列表
        """
        cart_url = 'https://cart.jd.com/cart.action'
        cart_header = u'|  购买  |  数量  |    价格    |    总价    |    商品'
        cart_format = u'|{0:7}| {1:6}| {2:11}| {3:11}| {4}'

        try:
            resp = self.session.get(cart_url, cookies=self.cookies)
            resp.encoding = 'utf-8'
            soup = bs4.BeautifulSoup(resp.text, "html.parser")

            print ''
            print '+++++++++++++++++++++++++++++++++++++++++++++++++++++++'
            print u'{0} > 购物车明细'.format(time.ctime())
            print '---------------------------------------------------------------------'
            print cart_header
            print '---------------------------------------------------------------------'

            for item in soup.select('div.item-form'):
                check = tags_val(item.select('div.cart-checkbox input'), key='checked')
                check = ' + ' if check else ' - '
                count = tags_val(item.select('div.quantity-form input'), key='value')
                price = tags_val(item.select('div.p-price strong'))
                sums = tags_val(item.select('div.p-sum strong'))
                gname = tags_val(item.select('div.p-name a'))
                #: ￥字符解析出错, 输出忽略￥
                print cart_format.format(check, count, price[1:], sums[1:], gname)

            t_count = tags_val(soup.select('div.amount-sum em'))
            t_value = tags_val(soup.select('span.sumPrice em'))
            print '---------------------------------------------------------------------'
            print u'|  总数  | {0}'.format(t_count)
            print '---------------------------------------------------------------------'
            print u'|  总额  | {0}'.format(t_value[1:])
            print '---------------------------------------------------------------------'

        except Exception, e:
            print 'Exp {0} : {1}'.format(FuncName(), e)

    def order_info(self, submit=False):
        """
        获取订单详情，并提交购买
        :param submit:
        :return:
        """
        print ''
        print '+++++++++++++++++++++++++++++++++++++++++++++++++++++++'
        print u'{0} > 订单详情'.format(time.ctime())

        try:
            order_url = 'http://trade.jd.com/shopping/order/getOrderInfo.action'
            payload = {
                'rid': str(int(time.time() * 1000)),
            }

            # get preorder page
            rs = self.session.get(order_url, params=payload, cookies=self.cookies)
            soup = bs4.BeautifulSoup(rs.text, "html.parser")

            # order summary
            payment = tag_val(soup.find(id='sumPayPriceId'))
            detail = soup.find(class_='fc-consignee-info')

            if detail:
                snd_usr = tag_val(detail.find(id='sendMobile'))
                snd_add = tag_val(detail.find(id='sendAddr'))


                print u'应付款：{0}'.format(payment)
                print snd_usr
                print snd_add

            # just test, not real order
            if not submit:
                return False

            # order info
            payload = {
                'overseaPurchaseCookies': '',
                'submitOrderParam.btSupport': '1',
                'submitOrderParam.ignorePriceChange': '0',
                'submitOrderParam.sopNotPutInvoice': 'false',
                'submitOrderParam.trackID': self.trackid,
                'submitOrderParam.eid': self.eid,
                'submitOrderParam.fp': self.fp,
            }

            order_url = 'http://trade.jd.com/shopping/order/submitOrder.action'
            rp = self.session.post(order_url, params=payload, cookies=self.cookies)

            if rp.status_code == 200:
                js = json.loads(rp.text)
                if js['success'] == True:
                    print u'下单成功！订单号：{0}'.format(js['orderId'])
                    print u'请前往东京官方商城付款'
                    return True
                else:
                    print u'下单失败！<{0}: {1}>'.format(js['resultCode'], js['message'])
                    if js['resultCode'] == '60017':
                        # 60017: 您多次提交过快，请稍后再试
                        time.sleep(1)
            else:
                print u'请求失败. StatusCode:', rp.status_code

        except Exception, e:
            print 'Exp {0} : {1}'.format(FuncName(), e)

        return False