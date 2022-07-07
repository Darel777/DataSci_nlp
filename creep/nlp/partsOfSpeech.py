import jieba
import jieba.posseg as pseg
import re
import json
from collections import defaultdict
import orderedset #pip install ordered-set
from setuptools._vendor.ordered_set import OrderedSet

# 添加自定义词典
jieba.load_userdict(r"my_dict.txt")

# 函数入口
def nlpDeal(str):
    save_file = "partsOfSpeech.json" #标注结果路径

    # 按照句号和逗号分句
    remove_full_point_list = re.split('。|\n', str)

    # 去除空字符（对应原文中的分段）
    while '' in remove_full_point_list:
        remove_full_point_list.remove('')

    # 根据词性分词，得到一个二维列表
    after_pseg = []
    for each in remove_full_point_list:
        after_pseg.append(pseg.lcut(each))

    ##########
    # 信息标注部分
    defendant_list = []  # 被告人
    sex_list = []  # 性别
    ethnic_list = []  # 民族
    birthPlace_list = []  # 出生地
    relatedCourt_set = set()  # 相关法院，仍需处理
    relatedCourt_list = set()  # 相关法院，处理结束
    cause_list = []  # 案由

    # 获取被告人，性别，民族和出生地
    temp_list = []
    temp_cause_list = []
    for each in remove_full_point_list:
        if (('被告人' in each) and (("男" in each) or ("女" in each))):
            temp_list.append(each)
        if "本院认为" in each:
            temp_cause_list.append(each)
    basic_information_list = []
    for each in temp_list:
        basic_information_list.append(each.split("，"))
    for i in basic_information_list:
        for j in i:
            if "被告人" in j:
                defendant_list.append(j[3:])
            if j == "男" or j == "女":
                sex_list.append(j)
            if "族" in j:
                ethnic_list.append(j)
            if "出生于" in j:
                birthPlace_list.append(j[j.index("出生于") + 3:])
            if "出生地" in j:
                birthPlace_list.append(j[j.index("出生地") + 3:])
            if "生于" in j and len(birthPlace_list) != len(defendant_list):
                birthPlace_list.append(j[j.index("生于") + 2:])
            if "户籍地" in j and len(birthPlace_list) != len(defendant_list):
                birthPlace_list.append(j[j.index("户籍地") + 3:])
            if "住" in j and len(birthPlace_list) != len(defendant_list):
                birthPlace_list.append(j[j.index("住") + 1:])
            if "户籍所在地" in j and len(birthPlace_list) != len(defendant_list):
                birthPlace_list.append(j[j.index("户籍所在地") + 5:])

    #处理自治区
    for i in range(len(ethnic_list)-1,-1,-1):
        if "自治" in ethnic_list[i]:
            ethnic_list.pop(i)

    # 处理（原审被告人）和告人
    for i in range(0,len(defendant_list)):
        if '（原审被告人）' in defendant_list[i]:
            defendant_list[i] = defendant_list[i].replace("（原审被告人）", "")
        if '(原审被告人)' in defendant_list[i]:
            defendant_list[i] = defendant_list[i].replace("(原审被告人)", "")
        if '告人' in defendant_list[i]:
            defendant_list[i] = defendant_list[i].replace("告人", "")
        if '诉人' in defendant_list[i]:
            defendant_list[i] = defendant_list[i].replace("诉人", "")

    #处理上诉情况下的被告人重复问题
    if len(defendant_list) != len(ethnic_list):
        temp_defendant_list = []
        temp_defendant = defendant_list[0]
        temp_defendant_list.append(defendant_list[0])
        for i in range(1,len(defendant_list)):
            if temp_defendant not in defendant_list[i]:
                temp_defendant=defendant_list[i]
                temp_defendant_list.append(temp_defendant)
        for each in defendant_list:
            if each not in temp_defendant_list:
                defendant_list.remove(each)


    # 相关法院
    for i in after_pseg:
        for word, flag in i:
            if "最高人民法院" in word:
                relatedCourt_set.add("中华人民共和国最高人民法院")
            if word == "高级人民法院":
                index_t = i.index(pseg.pair(word, flag))
                if (i[index_t - 1].flag == 'ns'):
                    relatedCourt_set.add(i[index_t - 1].word + i[index_t].word)
            if "高级人民法院" in word and word != "高级人民法院":
                relatedCourt_set.add(word)
            if word == "中级人民法院" or "人民法院":
                index_t = i.index(pseg.pair(word, flag))
                if (index_t + 1 < len(i)):
                    if (i[index_t - 1].flag == 'ns' and i[index_t - 2].flag == 'ns' and i[index_t + 1].word != '提出'):
                        relatedCourt_set.add(i[index_t - 2].word + i[index_t - 1].word + i[index_t].word)
                else:
                    if (i[index_t - 1].flag == 'ns' and i[index_t - 2].flag == 'ns'):
                        relatedCourt_set.add(i[index_t - 2].word + i[index_t - 1].word + i[index_t].word)
            if "中级人民法院" in word and word != "中级人民法院":
                relatedCourt_set.add(word)
        for each in relatedCourt_set:
            if "法院" in each:
                relatedCourt_list.add(each)

    # 获取案由
    temp_cause_remove_sign_list = []
    for each in temp_cause_list:
        temp = re.split("；|，", each)
        for i in temp:
            temp_cause_remove_sign_list.append(i)
    for each in temp_cause_remove_sign_list:
        if "行为" and "构成" in each:
            cause_list.append(each[each.index("构成") + 2:].replace("罪", ""))

        # 以下为存储到json文件
    key = ["noun", "verb", "adj", "adv"]
    noun = []
    verb = []
    adj = OrderedSet()
    adv = OrderedSet()
    noun[0:0] = defendant_list + sex_list + ethnic_list + birthPlace_list + list(relatedCourt_list)
    verb[0:0] = cause_list
    noun = OrderedSet(noun)
    verb = OrderedSet(verb)

    for i in range(max(8, len(after_pseg) - 15), len(after_pseg) - 10):
        for word, flag in after_pseg[i]:
            if (flag == "n" or "nz" or "nl" or "ng") and len(word) >= 2:
                noun.add(word)
                if len(noun) > 40:
                    break
    for i in range(0, len(after_pseg)):
        for word, flag in after_pseg[i]:
            if flag == "v" and len(word) >= 2:
                verb.add(word)
                if len(verb) > 30:
                    break
    for i in range(0, len(after_pseg)):
        for word, flag in after_pseg[i]:
            if (flag == "a"):
                adj.add(word)
                if len(adj) > 18:
                    break
    for i in range(0, len(after_pseg)):
        for word, flag in after_pseg[i]:
            if (flag == "ad"):
                adv.add(word)
                if len(adv) > 18:
                    break

    final_result = defaultdict(list)
    for i in range(0, 4):
        if i == 0:
            final_result[key[i]] = list(noun)
        if i == 1:
            final_result[key[i]] = list(verb)
        if i == 2:
            final_result[key[i]] = list(adj)
        if i == 3:
            final_result[key[i]] = list(adv)

    return json.dump(final_result)


