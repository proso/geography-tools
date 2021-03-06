# -*- coding: utf-8 -*-
from datetime import datetime
import pandas as pd


def normalize_by(answers, by):
    means = answers.groupby(by)['response_time'].mean()
    stds = answers.groupby(by)['response_time'].std()
    means_dict = {}
    for p, t in means.iteritems():
        means_dict[p] = {}
        means_dict[p]['mean'] = t
    for p, t in stds.iteritems():
        means_dict[p]['std'] = t
    rows = []
    for i, row in answers.iterrows():
        row['response_time'] = (row['response_time'] - means_dict[row[by]]['mean']) / means_dict[row[by]]['std']
        rows.append(row)
    return pd.DataFrame(rows)


def load_csv(csv_file):
    data = pd.DataFrame.from_csv(csv_file, index_col=False)
    for column in data.columns:
        if column == 'inserted':
            data['inserted'] = data['inserted'].apply(convert_time)
        elif column == 'id':
            data.sort(['id'], inplace=True, ascending=True)
        elif is_list_column(data[column]):
            data[column] = data[column].apply(lambda x: str2list(x, int))
    return data


def convert_time(value):
    return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")


def str2list(x, convert_item=None):
    s = x.strip('[]').replace(' ', '').split(',')
    if convert_item:
        s = map(convert_item, s)
    return s


def is_list_column(column):
    if len(column) == 0:
        return False
    reps = column.head(min(10, len(column)))
    str_type = type('')
    return reps.apply(lambda x: type(x) == str_type and x.startswith('[') and x.endswith(']')).all()


def floyd_warshall(distance_matrix):
    vertices = distance_matrix.keys()
    d = dict(distance_matrix)   # copy
    for k in vertices:
        for i in vertices:
            for j in vertices:
                d[i][j] = min(d[i][j], d[i][k] + d[k][j])
    return d
