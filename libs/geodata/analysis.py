import sys
from geodata import Answers, Places
import matplotlib.pyplot as plt
import scipy.stats as stats
import numpy as np
import pandas as pd
from pprint import pprint


class GeneralAnalysis:

    def __init__(self, filename_csv = None, answers = None):
        if filename_csv:
            self.answers = Answers.from_csv(filename_csv)
        elif answers:
            self.answers = answers
        else:
            raise Exception("Can't create a new analysis object.")

    def __getitem__(self, key):
        if np.isscalar(key):
            return self.answers[key]
        else:
            return self.new_from_answers(self.answers[key])

    def __setitem__(self, key, value):
        self.answers[key] = value

    def new_from_answers(self, answers):
        raise Exception("Method 'new_from_answers should be overriden.")

class PlotAnalysis(GeneralAnalysis):

    def __init__(self, filename_csv = None, answers = None):
        GeneralAnalysis.__init__(self, filename_csv, answers)

    def plot_time_hist(self, correct = True):
        xmax = max(
            self.answers.wrong_answers()["response.time"].max(),
            self.answers.correct_answers()["response.time"].max())
        data = None
        color = None
        label = None
        if correct:
            data = self.answers.correct_answers()
            color = "green"
            label = "Correct Answers"
        else:
            data = self.answers.wrong_answers()
            color = "red"
            label = "Wrong Answers"
        plt.hist(
            data['response.time'],
            bins = 20,
            color = color,
            label = label)
        plt.xlabel("Response Time (log)")
        plt.xlim(0, xmax)

    def plot_time_density(self, correct = True):
        xmax = max(
            self.answers.wrong_answers()["response.time"].max(),
            self.answers.correct_answers()["response.time"].max())
        data = None
        color = None
        label = None
        if correct:
            data = self.answers.correct_answers()
            color = "green"
            label = "Correct Answers"
        else:
            data = self.answers.wrong_answers()
            color = "red"
            label = "Wrong Answers"
        xs = np.linspace(0,xmax,1000)
        density = stats.gaussian_kde(data['response.time'])
        plt.plot(xs, density(xs), color = color, label = label)
        plt.xlabel("Response Time (log)")
        plt.ylabel("Probability")

    def plot_pattern_times_density(self, pattern, plot, labels, normalize = None):
        if len(pattern) != len(plot):
            raise Exception("The length of pattern and plot lists doesn't match")
        data = self._get_pattern_times(pattern, normalize = normalize)
        xmin = min(map(lambda df: df['response.time'].min(), data))
        xmax = max(map(lambda df: df['response.time'].max(), data))
        xs = np.linspace(xmin, xmax, 1000)
        for i in range(len(pattern)):
            if plot[i]:
                plt.plot(
                    xs,
                    stats.gaussian_kde(data[i]['response.time'])(xs),
                    label = labels[i])

    def _get_pattern_times(self, pattern, normalize = None):
        data = self.answers
        data = data.sort(['place.asked', 'inserted'])
        data['response.time'] = np.log(data['response.time'])
        if normalize != None:
            data.normalize_response_time(normalize, inplace = True)
        data = data.data
        result = []
        for i in pattern:
            result.append(pd.DataFrame())
        search = []
        for user in data['user'].unique():
            user_data = data[data['user'] == user]
            for i, row in user_data.iterrows():
                search.append(row)
                if len(search) < len(pattern):
                    continue
                elif len(search) > len(pattern):
                    search = search[1:]
                pattern_match = True
                for i in range(len(pattern)):
                    if pattern[i] != (
                        search[i]['place.asked'] == search[i]['place.answered']):
                        pattern_match = False
                        break
                if not pattern_match:
                    continue
                for i in range(len(pattern)):
                    result[i] = result[i].append(pd.DataFrame([search[i].to_dict()]))
        return result

    def new_from_answers(self, answers):
        return PlotAnalysis(answers = answers)


class MapAnalysis(GeneralAnalysis):

    def __init__(self, kartograph, shapefile, places_csv = None, places_dataframe = None, answers_csv = None, answers_dataframe = None):
        GeneralAnalysis.__init__(self, answers_csv, answers_dataframe)
        if places_csv:
            self.places = Places.from_csv(places_csv)
        else:
            self.places = places_dataframe
        self.shapefile = shapefile
        self.kartograph = kartograph

    def new_from_answers(self, answers):
        return MapAnalysis(
            kartograph = self.kartograph,
            shapefile = self.shapefile,
            places_dataframe = self.places,
            answers_dataframe = answers)

    def success_probability(self, out_svg):
        data = []
        for place in self.answers['place.asked'].unique():
            place_code = self.places[self.places['id'] == place].head()['code']
            place_code = list(place_code)[0]
            place_data = self.answers[self.answers['place.asked'] == place]
            success = place_data['place.asked'] == place_data['place.answered']
            data.append({
                'code'  : place_code,
                'ratio' : float(sum(success)) / len(place_data)})
        self._save(
            pd.DataFrame(data),
            self._config_world(),
            out_svg,
            out_svg + ".css")

    # data - code, ratio
    def _save(self, data, config, out_svg, out_css):
        self._create_css(data, out_css)
        css = open(out_css)
        self.kartograph.generate(
            config,
            outfile = out_svg,
            stylesheet = css.read())

    def _config_world(self):
        layer = {
            'src'   : self.shapefile,
            'class' : 'states'
        }
        return {'layers' : [layer]}

    def _create_css(self, data, filename):
        try:
            file = open(filename, 'w')
            for i, row in data.iterrows():
                code = row['code'].upper()
                ratio = row['ratio']
                file.write('.states[iso_a2=' + code + '] { fill: ' + self._color_rgspectrum(ratio) + '; }\n')
            file.close()
        finally:
            pass

    def _color_rgspectrum(self, val): # val 0..1
        if val < 0 or val > 1:
            raise Exception("The value has to be from [0,1] interval.")
        val = 1 - (1-val)*2
        r = int(255 * val)
        g = int(255 * val)
        b = int(255 * val)
        return "'rgb("+`r`+','+`g`+','+`b`+")'"
