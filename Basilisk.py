import sys
import numpy as np


class PatternContext:
    def __init__(self, initial_noun):
        self.score = 0
        self.head_nouns = [initial_noun]


class Basilisk:

    def __init__(self, seeds_path, contexts_path):
        self.seeds = self.parse_intial_seed_words(seeds_path)
        self.lexicon = self.seeds.copy()
        self.patterns = self.parse_intial_patterns(contexts_path)

        self.pattern_pool = {}
        self.candidate_list = {}
        self.avg_log = {}
        self.new_words = {}

    @staticmethod
    def parse_intial_seed_words(seeds_path):
        with open(seeds_path, 'r') as file:
            seeds = [line.lower()[:-1] for line in file]
        return seeds

    @staticmethod
    def parse_intial_patterns(contexts_path):
        patterns = {}
        with open(contexts_path, 'r') as file:
            for line in file:
                line_arr = line.split()
                i = 0
                while line_arr[i] != '*':
                    head_noun = line_arr[i]
                    i += 1
                pattern = line_arr[-1]

                if pattern in patterns:
                    if head_noun.lower() not in patterns[pattern].head_nouns:
                        patterns[pattern].head_nouns.append(head_noun.lower())
                else: patterns[pattern] = PatternContext(head_noun.lower())

        return patterns

    def score_patterns(self):
        for pattern, context in self.patterns.items():
            semfreq = 0
            for lex in self.lexicon:
                if lex in context.head_nouns:
                    semfreq += 1
            totalfreq = len(context.head_nouns)
            if semfreq != 0: context.score = self.rlogf(semfreq, totalfreq)

    @staticmethod
    def rlogf(semfreq, totalfreq):
        return (semfreq / totalfreq) * np.log2(semfreq)

    def sort_patterns(self):
        self.pattern_pool = {}
        sorted_patterns = sorted(self.patterns, key=lambda pattern:self.patterns[pattern].score)

        for i in range(len(sorted_patterns) - 1, -1, -1):
            if i == len(sorted_patterns) - 10:
                last = self.patterns[sorted_patterns[i]].score
            elif i < len(sorted_patterns) - 10 and self.patterns[sorted_patterns[i]].score != last:
                break

            if self.patterns[sorted_patterns[i]].score == 0:
                break
            self.pattern_pool[sorted_patterns[i]] = self.patterns[sorted_patterns[i]]

    def get_candidates(self):
        self.candidate_list = {}
        for pattern, context in self.pattern_pool.items():
            for head_noun in context.head_nouns:
                self.candidate_list[head_noun] = []

    def score_candidates(self):
        self.avg_log = {}
        for pattern, context in self.patterns.items():
            for word in self.candidate_list.keys():
                if word in context.head_nouns:
                    self.candidate_list[word].append(pattern)

        for word, patterns in self.candidate_list.items():
            freq = [0 for _ in range(len(patterns))]
            for i in range(len(patterns)):
                for lex in self.lexicon:
                    if lex in self.patterns[patterns[i]].head_nouns:
                        freq[i] += 1

            avg = 0
            for f in freq:
                avg += np.log2(f + 1)
            avg /= len(patterns)
            self.avg_log[word] = avg

    def sort_candidates(self):
        self.new_words = {}
        sorted_avg_log = sorted(self.avg_log, key=lambda word:self.avg_log[word], reverse=True)
        i = 0
        count = 0

        for avg_word in sorted_avg_log:
            if avg_word not in self.lexicon:
                if count == 4:
                    last = self.avg_log[sorted_avg_log[i]]
                elif count > 4 and self.avg_log[sorted_avg_log[i]] != last:
                    break

                self.lexicon.append(avg_word)
                self.new_words[avg_word] = self.avg_log[avg_word]
                count += 1
            i += 1

    def print_iter(self, iter, f):
        f.write('\nITERATION ' + str(iter) + '\n\n')
        f.write('PATTERN POOL\n')
        i = 1
        pattern_list = sorted(self.pattern_pool.items(), key=lambda pattern: (-pattern[1].score, pattern[0]))
        for pattern, context in pattern_list:
            score = round(context.score, 3)
            score = format(score, '.3f')
            f.write(str(i) + '. ' + pattern + '  (' + str(score) + ')\n')
            i += 1

        f.write('\nNEW WORDS\n')

        sorted_new_words = sorted(self.new_words.items(), key=lambda word: (-word[1], word[0]))

        for word, score in sorted_new_words:
            score = format(round(score, 3), '.3f')
            f.write(word + '  (' + str(score) + ')\n')

    def run(self, file_name, num_iterations=5):
        f = open(file_name + ".trace", "w+")
        f.write('\nSeed Words: ' + ' '.join(self.seeds) + '\n')
        f.write('Unique patterns: ' + str(len(self.patterns)) + '\n')
        for i in range(num_iterations):
            self.score_patterns()
            self.sort_patterns()
            self.get_candidates()
            self.score_candidates()
            self.sort_candidates()
            self.print_iter(i + 1, f)
        f.close()


if __name__ == "__main__":
    seeds_file = sys.argv[1]
    contexts_file = sys.argv[2]
    basilisk = Basilisk(seeds_file, contexts_file)

    seed_end = 0
    seed_start = 0
    for i in range(len(seeds_file)):
        if seeds_file[i] == '/':
            seed_start = i + 1
        elif seeds_file[i] == '-':
            seed_end = i

    context_end = 0
    context_start = 0
    for i in range(len(contexts_file)):
        if contexts_file[i] == '/':
            context_start = i + 1
        elif contexts_file[i] == '-':
            context_end = i

    out_file = seeds_file[seed_start:seed_end] + '-' + contexts_file[context_start:context_end]
    basilisk.run(out_file)

