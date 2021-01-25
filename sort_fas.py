# -*- coding: utf-8 -*-
"""
Created on Fri Jan 22 02:38:04 2021

@author: Chengxi Luo
"""
DEPTH = 1000

def rbo(run, ideal, p):
    run_set = set()
    ideal_set = set()

    score = 0.0
    normalizer = 0.0
    weight = 1.0
    for i in range(DEPTH):
        if i < len(run):
            run_set.add(run[i])
        if i < len(ideal):
            ideal_set.add(ideal[i])
        score += weight*len(ideal_set.intersection(run_set))/(i + 1)
        normalizer += weight
        weight *= p
    return score/normalizer
    
import random
import math
import csv
import re
import argparse


class graph():
    def __init__(self):
        self.indict = {}
        self.outdict = {}
        self.nodes = set()

    def add_edge(self, f, t):
        self.outdict[f] = self.outdict.setdefault(f, nodeInfo()).add(t)
        self.indict[t] = self.indict.setdefault(t, nodeInfo()).add(f)
        self.nodes.add(f)
        self.nodes.add(t)
        return self

    def remove_edge(self, f, t):
        self.outdict[f] = self.outdict.setdefault(f, nodeInfo()).remove(t)
        self.indict[t] = self.indict.setdefault(t, nodeInfo()).remove(f)
        if self.indict[f] == 0 and self.outdict[f] == 0:
            self.nodes.remove(f)
        if self.outdict[t] == 0 and self.indict[t] == 0:
            self.nodes.remove(t)
        return self

    def remove_node(self, node):
        for in_node in self.getInNodes(node):
            self.outdict[in_node].remove(node)
        if node in self.indict:
            self.indict.pop(node)

        for out_node in self.getOutNodes(node):
            self.indict[out_node].remove(node)
        if node in self.outdict:
            self.outdict.pop(node)

        self.nodes.remove(node)
        return self

    def getInNodes(self, node):
        if node not in self.nodes:
            raise ValueError()
        if node not in self.indict:
            return  []
        return self.indict[node].nodes

    def getOutNodes(self, node):
        if node not in self.nodes:
            raise ValueError()
        if node not in self.outdict:
            return  []
        return self.outdict[node].nodes


class nodeInfo():
    def __init__(self):
        self.degree = 0
        self.nodes = []

    def add(self, node):
        self.nodes.append(node)
        self.degree += 1
        return self

    def remove(self, node):
        self.nodes.remove(node)
        self.degree -= 1
        return self

    def remove_all(self, node):
        while node in self.nodes:
            self.nodes.remove(node)
            self.degree -= 1
        return self

    def degree(self):
        return self.degree

def readQPrefs(file_name):
    jud = {}
    doc = {}
    with open(file_name) as f:
        for line in f:
            jObj = re.split("\s|(?<!\d)[,.](?!\d)", line.strip())
            jud[jObj[0]] = jud.setdefault(jObj[0], graph()).add_edge(jObj[1], jObj[2])
            if jObj[0] not in doc:
                doc[jObj[0]] = set()
            doc[jObj[0]].add(jObj[1])
            doc[jObj[0]].add(jObj[2])

    return jud,doc

def open_actual_rank(filename):
    actual_rank = {}
    currentTopic = ''
    with open(filename) as f:
        for line in f:
            jObj = re.split("\s|(?<!\d)[,.](?!\d)", line.strip())
            currentTopic = jObj[0]
            if currentTopic in actual_rank:
                actual_rank[currentTopic][jObj[2]]=int(jObj[3])
            else:
                actual_rank[currentTopic] = {}
                actual_rank[currentTopic][jObj[2]]=int(jObj[3])
    return actual_rank

def write_csvfile(filename, content_dict):
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=' ')

        for topic in content_dict:
            num = 0
            for doc in content_dict[topic]:
                num+=1
                writer.writerow([topic, 0, doc, num])

def get_sorted_key(dictionary):
    return [key for key,value in sorted(dictionary.items(), key = lambda item:item[1])]

def get_full_nodes(doc, sorted_key):
    linear_arr = sorted_key
    for i in doc:
        if i not in sorted_key:
            linear_arr.append(i)
    return linear_arr

def get_less_nodes(doc, sorted_key):
    linear_arr = []
    for i in sorted_key:
        if i in doc:
            linear_arr.append(i)
    return linear_arr

def sort_fas(judgements, actual_rank, doc):
    #linear_arr1 = get_sorted_key(actual_rank)
    linear_arr = get_less_nodes(doc, get_sorted_key(actual_rank))
    linear_arr.reverse()
    #random.shuffle(linear_arr)
    result = []
    for i in range(len(linear_arr)):
        val = 0
        min = 0
        loc = i
        for j in range(i-1, -1, -1):
            w = result[j]
            if linear_arr[i] in judgements.outdict:
                if w in judgements.outdict[linear_arr[i]].nodes:
                    val -= 1
            elif linear_arr[i] in judgements.indict:
                if w in judgements.indict[linear_arr[i]].nodes:
                    val += 1
            if val <= min:
                min = val
                loc = j
        result.insert(loc, linear_arr[i])
    return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
    description='Ranking by greedy feedback arc set')
    parser.add_argument('prefs', type=str, help='Preferences judgments')
    parser.add_argument('run', type=str, help='Actual search results')
    args = parser.parse_args()

    hiQ_filename = args.prefs
    actualrank_filename = args.run
    
    #hiQ_filename = 'waterloo.pref'
    #actualrank_filename = 'input.clacBase'

    #print('Start reading hiQ file:', hiQ_filename)
    judgements_graph, doc = readQPrefs(hiQ_filename)


    #print('Start reading actual ranking file:', actualrank_filename)
    actual_rank = open_actual_rank(actualrank_filename)


    #print('Start computing ideal ranking.')

    print('runid,topic,compatibility')
    total = 0.0
    N = 0
    fas_rank = {}
    #print('Start computing ideal ranking.')
    for topic in judgements_graph:
        rank = sort_fas(judgements_graph[topic], actual_rank[topic], doc[topic])
        fas_rank[topic] = rank
        actual = list(actual_rank[topic].keys())
        actual.sort(key=lambda docno: actual_rank[topic][docno])
        score = rbo(rank, actual, 0.80)
        print(actualrank_filename, topic, score, sep=',')
        total += score
        N += 1
    if N > 0:
        print(actualrank_filename, 'amean', total/N, sep=',')
    else:
        print(actualrank_filename, 'amean, 0.0')

    #Write ideal ranking file
    #write_csvfile(actualrank_filename+'_sortfas_idealrank', fas_rank)

    #print('Finish writing ideal ranking file:', actualrank_filename+'_idealrank')

