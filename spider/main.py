# -*- coding = utf-8 -*-
# @Time : 2021/6/4 20:29
# @Author : 黄鹏龙
# @File : main.py
# @Software : PyCharm


# 需要用到的库
import re                             # 正则表达式
import urllib.request                 # 给定URL，获取相应的网页
import urllib.error
import sqlite3
from bs4 import BeautifulSoup         # 拿到网页数据，将其解析成一颗树
from urllib import parse
import pandas as pd


def spider():
    userinput = input("请输入您要爬取的岗位关键字：")
    searchword = parse.quote(parse.quote(userinput))
    firsturl = "https://search.51job.com/list/040000,000000,0000,00,9,99," + searchword + ",2,"
    suburl = ".html?lang=c&postchannel=0000&workyear=99&cotype=99&degreefrom=99&jobterm=99&companysize=99&ord_field=0&dibiaoid=0&line=&welfare="
    pagenum = 10  # 一页50条数据

    # 1、爬取网页 2、解析数据

    datalist = getData(firsturl, suburl, pagenum)
    print("爬取数据(共有%d条数据)成功，正在准备处理数据..." % len(datalist))

    # 3、处理缺失值
    print("正在处理缺失值（取均值）......")
    datalist = fillna_datalist(datalist)

    # 4、保存数据

    save2sqlite(r'..\db\51jobDatabase.db', datalist)
    print("处理数据成功，保存到数据库成功！")

# 处理缺失值
def fillna_datalist(datalist):

    dataframe = pd.DataFrame(datalist,
                             columns=['cname', 'jobname', 'minisalary', 'maxsalary', 'workplace', 'welfare', 'askexp',
                                      'askdegree'])
    # 数据预处理1：更改某些属性的数据类型
    # 将数据库中的‘最低薪资’的数据类型改成float
    sr_minisalary = dataframe['minisalary']
    sr_minisalary = pd.to_numeric(sr_minisalary)

    # 将数据库中的‘最高薪资’的数据类型改成float
    sr_maxsalary = dataframe['maxsalary']
    sr_maxsalary = pd.to_numeric(sr_maxsalary)

    # 更改dataframe的属性
    dataframe['minisalary'] = sr_minisalary
    dataframe['maxsalary'] = sr_maxsalary

    # 数据预处理2：处理缺失值
    dataframe['minisalary'].fillna(dataframe['minisalary'].mean(), inplace=True)
    dataframe['maxsalary'].fillna(dataframe['maxsalary'].mean(), inplace=True)
    datalist = dataframe.values
    return datalist

def getData(firsturl,suburl,pagenum):
    datalist = []

    for i in range(1, pagenum+1):

        # 1、拼接url
        url = firsturl + str(i) + suburl

        # 2、访问url，爬取数据
        print(url)
        html = askURL(url)

        # 3、将数据进行解析，并定位到需要的内容块
        soup = BeautifulSoup(html, "html.parser")
        scriptlist = soup.find_all('script')        # 找到所有script标签包含的内容并且用列表的方式返回
        data_str = str(scriptlist[7])

        # 4、将内容块中的数据截取出来,用正则表达式来一一匹配
        # 公司名字
        company_name = re.findall(re.compile(r'"company_name":(.*?),'), data_str)
        # 职位名称
        job_name = re.findall(re.compile(r'"job_name":(.*?),'), data_str)
        # 提供薪资（区间）
        providesalary_text = re.findall(re.compile(r'"providesalary_text":(.*?),'), data_str)
        # 工作地区
        workarea_text = re.findall(re.compile(r'"workarea_text":(.*?),'), data_str)
        # 公司福利
        jobwelf_text = re.findall(re.compile(r'"jobwelf":(.*?),'), data_str)
        # 要求经验、要求学历
        attribute_text = re.findall(re.compile(r'"attribute_text":(.*?)],'), data_str)

        # 5、清洗数据，将数据包装，对接数据库的接口
        for i in range(0, 50):
            data = []

            # 1、公司名字
            data.append(str(company_name[i]).replace('"', ''))

            # 2、职位名称
            data.append(str(job_name[i]).replace('"', ""))

            # 3、薪资区间

            # 若查出来的数据中薪资的单位为：千 或 年，则将这样的薪资设置为空（后期会将该职位信息删除）
            isw = True
            ism = True
            if (providesalary_text[i].find('千')) != -1:
                isw = False
            if (providesalary_text[i].find('年')) != -1:
                ism = False
            salarylist = re.findall("\d+\.?\d?", providesalary_text[i])
            # print(salarylist)

            if len(salarylist) == 2 and isw == True and ism == True:
                data.append(salarylist[0])
                data.append(salarylist[1])
            elif len(salarylist) == 2 and isw == False:
                data.append(str(float(salarylist[0])/10))
                data.append(str(float(salarylist[1])/10))
            elif len(salarylist) == 2 and ism == False:
                data.append(str(round(float(salarylist[0])/12, 2)))
                data.append(str(round(float(salarylist[1])/12, 2)))
            else:
                data.append('')
                data.append('')


            # 4、工作地区
            data.append(str(workarea_text[i]).replace('"', ""))

            # 5、公司福利
            data.append(str(jobwelf_text[i]).replace('"', ""))

            # 6、要求经验
            curattribute_text = attribute_text[i].split(",")

            askedexperience = curattribute_text[1].replace('"', '')[0]
            if(askedexperience)!='无' and (askedexperience)!='招' and (askedexperience)!='大' and (askedexperience)!='本' and (askedexperience)!='硕' and (askedexperience)!= '中':
                data.append(askedexperience)
            else:
                data.append('0')

            # 7、要求学历
            # 若爬取的数据中有要求学历的信息，则记录下对应的数据
            if len(curattribute_text)>=3:
                askeddegree = curattribute_text[2].replace('"', '')
                if(askeddegree.find('招'))!=-1:
                    data.append('其他')
                else:
                    data.append(askeddegree)
            # 否则，标记为其他
            else:
                data.append('其他')


            # 8、封装数据
            datalist.append(data)
    return datalist

def askURL(url):
    # 伪装一个请求对象，准备访问url
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    req = urllib.request.Request(url=url, headers=headers)

    # 使用自定义的请求对象访问url，获得响应对象
    response = urllib.request.urlopen(req)

    # 解析数据
    html = response.read().decode('gbk')

    return html


def initsqlite(savepath):
    conn = sqlite3.connect(savepath)
    cur = conn.cursor()
    sql = """
        create table data_51job
        (
            id integer primary key autoincrement,
            company_name text not null,
            job_name  varchar not null,
            minisalary varchar not null,
            maxsalary varchar not null,
            workarea varchar not null,
            welfare text not null,
            askedexp varchar not null,
            askdegree varchar not null
        )
    """

    cur.execute(sql)
    conn.commit()

    cur.close()
    conn.close()


def save2sqlite(savepath,datalist):
    # 1、初始化数据库
    # initsqlite(savepath)        # 若没有创建数据库表则执行该语句进行创建

    conn = sqlite3.connect(savepath)
    cur = conn.cursor()

    # 2、执行插入语句之前，把表中的数据删除干净,并将自增列归零
    sql_delete = """
        delete from data_51job where 1=1
    """
    sql_updateseq = """
        update sqlite_sequence SET seq = 0 where name = 'data_51job';
    """
    cur.execute(sql_delete)
    cur.execute(sql_updateseq)
    conn.commit()


    # 3、执行插入语句，把爬取的数据存储到数据库中
    for dataitem in datalist:
        for i in range(0, len(dataitem)):
            if i==2 or i==3:
                dataitem[i] = str(dataitem[i])
            dataitem[i] = '"' + dataitem[i] + '"'

        # 执行插入语句
        sql_insert = """
            insert into data_51job
            (
            company_name,job_name,minisalary,maxsalary,workarea,welfare,askedexp,askdegree
            )
            values(%s)
        """ % ','.join(dataitem)

        cur.execute(sql_insert)
        conn.commit()
    cur.close()
    conn.close()




if __name__ == '__main__':
    spider()

