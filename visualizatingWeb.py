# -*- coding = utf-8 -*-
# @Time : 2021/7/8 13:16
# @Author : 黄鹏龙
# @File : visualizatingWeb.py
# @Software : PyCharm
from flask import Flask, render_template
import sqlite3

app = Flask(__name__)


@app.route('/')
def qiancheng_index():
    # 1、连接数据库并获取游标
    conn = sqlite3.connect(r"db\51jobDatabase.db")
    cur = conn.cursor()

    # 2、查询数据库并且将查询到的数据保存下来

    # 2.1 查询平均薪资对应的数量
    sql_count_avgsalary = r"select round((minisalary+maxsalary)/2.0, 2) as avgsalary,count((minisalary+maxsalary)/2) from data_51job group by minisalary order by avgsalary desc"
    data = cur.execute(sql_count_avgsalary)
    t1_minisalary = []
    t1_count_avgsalary = []
    for item in data:
        t1_minisalary.append(item[0])
        t1_count_avgsalary.append(item[1])

    # 2.2 查询公司名对应的平均薪资
    sql_companyname_avgsalary = r"select company_name,round((minisalary+maxsalary)/2.0, 2) as avgsalary from data_51job order by avgsalary desc"
    data = cur.execute(sql_companyname_avgsalary)
    t2_companyname = []
    t2_count_avgsalary = []
    for item in data:
        t2_companyname.append(item[0])
        t2_count_avgsalary.append(item[1])


    # 2.3 查询工作经验对应的平均薪资
    sql_exp_avgsalary = r"select round(avg((minisalary+maxsalary)/2.0),2) as avgsalary, askedexp from data_51job group by askedexp order by askedexp"
    data = cur.execute(sql_exp_avgsalary)
    t3_data = []
    for item in data:
        t3_list = [item[0], item[1]+'年工作经验']
        t3_data.append(t3_list)


    # 2.3 查询学历对应的平均薪资
    sql_degree_avgsalary = r"""
        select askdegree,round(avg((minisalary+maxsalary)/2.0),2) as avgsalary,count(id) as 职位个数
        from data_51job
        group by askdegree
        order by avgsalary desc
    """
    data = cur.execute(sql_degree_avgsalary)
    t4_data = []
    for item in data:
        t4_data.append([item[1], item[0]])

    # 3、关闭游标和链接
    cur.close()
    conn.close()
    return render_template("qiancheng_index.html", t1_minisalary = t1_minisalary, t1_count_minisalary = t1_count_avgsalary
                           , t2_companyname = t2_companyname, t2_count_avgsalary = t2_count_avgsalary
                           , t3_data = t3_data
                           , t4_data = t4_data)


if __name__ == '__main__':
    app.run()