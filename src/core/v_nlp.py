
import spacy
import numpy as np

# a library for spell-checking and Engish Word Detection
# import enchant

import re

from src.core.v_parser import compareFontStrings
from src.core.v_logger import info, error

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from textblob import TextBlob

import random
import uuid
from spacy.lang.en.stop_words import STOP_WORDS

class NlpWrapper:

    def __init__(self, mode):
        self.nlp = self.initialize()
        # self.enchant = enchant.Dict("en_US")
        self.enchant = None
        self.vader = SentimentIntensityAnalyzer()

    def initialize(self):


        nlp = spacy.load("en_core_web_sm")
        # Create the pipeline 'sentencizer' component
        # sbd = nlp.crea_pipe('sentencizer')
        # Add the component to the pipeline
        nlp.add_pipe('sentencizer')

        # nlp.add_pipe(PySBDFactory(nlp))

        info("NlpWrapper initialize done")
        return nlp

    def score(self, span):
        digest = self.nlp(span)
        features = {}

        features["english"] = sum(
            [1 for token in digest if self.enchant.check(token.text)])
        features["punct"] = sum([1 for token in digest if token.is_punct])
        features["num"] = sum([1 for token in digest if token.pos_ == "NUM"])
        features["sent"] = sum([1 for token in digest if token.is_sent_start])
        features["stop"] = sum([1 for token in digest if token.is_stop])
        features["has_vec"] = sum([1 for token in digest if token.has_vector])
        features["vec"] = sum(
            [token.vector for token in digest if token.has_vector]) / features["has_vec"]
        features["cls"] = sum(
            [token.cluster for token in digest]) / len(digest)
        features["total"] = len(digest)

        flat = []

        for feature in features.items():

            if isinstance(feature[1], np.ndarray):
                for item in feature[1]:
                    flat.append(item)
            else:
                flat.append(feature[1])

        return flat, features

    # modified levenshtein min ditance of two seq of characters
    def levenshtein(self, seq1, seq2):
        size_x = len(seq1) + 1
        size_y = len(seq2) + 1

        matrix = np.zeros((size_x, size_y))
        for x in range(size_x):
            matrix[x, 0] = x
        for y in range(size_y):
            matrix[0, y] = y

        for x in range(1, size_x):
            for y in range(1, size_y):
                if seq1[x - 1] == seq2[y - 1]:
                    matrix[x, y] = min(
                        matrix[x - 1, y] + 1,
                        matrix[x - 1, y - 1],
                        matrix[x, y - 1] + 1
                    )
                else:
                    matrix[x, y] = min(
                        matrix[x - 1, y] + 1,
                        matrix[x - 1, y - 1] + 1,
                        matrix[x, y - 1] + 1
                    )

        min_distance = (matrix[size_x - 1, size_y - 1])
        len_diff = abs(len(seq1) - len(seq2))

        return ((min_distance - len_diff) / len(seq2))

    # comparing to strings, finding one in another
    def compare(self, str1, ref_str):
        result = 1.0

        if isinstance(str1, str) and isinstance(ref_str, str):
            str1 = re.sub(r'\W+', ' ', str1.lower()).strip().split(" ")
            ref_str = re.sub(r'\W+', ' ', ref_str.lower()).strip().split(" ")
            result = self.levenshtein(str1, ref_str)
        else:
            info(Exception("v_nlp.compare Input format error!!"))

        return result

    def getVaderSentiment(self, input_string):
        input_string = re.sub(r'\n+', ' ', input_string).strip()
        vs = self.vader.polarity_scores(input_string)
        return vs

    def getTextBlobSentiment(self, input_string):
        input_string = re.sub(r'\n+', ' ', input_string).strip()
        return TextBlob(input_string).sentiment
    
    # This function has been used to remove not ascii characters
    # TODO:: silly name
    def cleanString(self, input_string):
        if isinstance(input_string, str) and input_string != "":
            return re.sub(r'\W+', '', input_string).strip()
        else:
            return ""

    def extractInformativeWords(self, input_string):
        digest = self.nlp(input_string)
        result = []
        for token in digest:
            if not token.is_punct and \
               not token.is_stop and not token.is_space:
                result.append(str(token))
        info("Set of informative words: " + str(result))
        return result

    def extractCitations(self, paper, section_index):
        start_index, end_index = paper.getSectionBoundary(section_index)
        text = ""

        for i in range(start_index, end_index):
            if compareFontStrings(
                    paper.x_lines[i]["font"], paper.main_font) != 1:
                text += paper.x_lines[i]["text"]
            else:
                info("skipping line for font")
                info(paper.x_lines[i]["text"])
                info(paper.x_lines[i]["font"])
                info("-----------------------")

        digest = self.nlp(text)
        sent_list = list(digest.sents)

        for i in range(len(sent_list)):
            sent = sent_list[i]
            if i > 0:
                sent_1 = sent_list[i - 1].text
            else:
                sent_1 = ""

            if i > 1:
                sent_2 = sent_list[i - 2].text
            else:
                sent_2 = ""

            cite_text = sent_2 + sent_1 + sent.text
            # TODO:: add other citation formats
            cites = re.findall(r"\[[\d+,*]+\]", sent.text)
            for j in range(len(cites)):
                cite_tags = cites[j][1:-1].split(",")
                for tag in cite_tags:
                    paper.cites[tag].append(cite_text)

        return paper

    def extractSections(self, paper):
        # candidcates based on hierarchal patterns
        h_cands = []
        # candidcates based on font
        f_cands = []
        # candidcates based on text
        s_cands = []
        # double candidates
        d_cands = []

        section_topic_candidates = ["abstract",
                                    "introduction",
                                    "background",
                                    "references",
                                    "discussion",
                                    "related",
                                    "conclusion",
                                    "acknowledgement",
                                    "appendix",
                                    "methodology"]
        hierarchy_patterns = [r"^\s*(\d+\s*\.*\s*)+\W+\w+",
                              r"^M{0,4}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})\W+\w+"]

        for i, xline in enumerate(paper.x_lines):
            # find all references section candidates

            for pattern in hierarchy_patterns:
                if re.search(pattern, xline["text"]):
                    h_cands.append(i)
                    break

            for candidate in section_topic_candidates:
                if candidate in xline["text"].lower()[:min(
                        15, len(xline["text"]))]:
                    s_cands.append(i)
                    break

            if i + 1 < len(paper.x_lines):
                next_line = paper.x_lines[i + 1]
            else:
                next_line = xline

            # section title candidate
            comp = compareFontStrings(xline["font"], next_line["font"])
            if comp == 1:
                f_cands.append(i + 1)
            elif comp == -1:
                if len(f_cands) > 0 and f_cands[-1] == i:
                    d_cands.append(i)
                else:
                    f_cands.append(i)

        candidates = []
        for c in f_cands:
            flag = False

            for c2 in d_cands:
                if c == c2:
                    candidates.append(c)
                    flag = True
                    break

            if not flag:
                for c2 in s_cands:
                    if c == c2:
                        candidates.append(c)
                        flag = True
                        break

            #print("\n\nHirarichy Candidates")
            if flag == False:
                for c2 in h_cands:
                    if c == c2:
                        candidates.append(c)
                        break
        levels = {}
        for i in candidates:
            c = paper.x_lines[i]
            # print(c)
            font_size = c["font"].split("-")[-1]
            if font_size in levels:
                if c["font"] in levels[font_size]:
                    levels[font_size][c["font"]].append(i)
                else:
                    levels[font_size][c["font"]] = [i]
            else:
                levels[font_size] = {c["font"]: [i]}

        levels = dict(
            sorted(levels.items(), key=lambda item: float(item[0]), reverse=True))

        section_title_indices = []
        ref_section_found = False
        ref_start_index = 0
        for level in levels:
            # print(level)
            for font in levels[level]:
                # print(font)
                for index in levels[level][font]:
                    # print(paper.x_lines[index])
                    # font category for section titles found
                    if "reference" in paper.x_lines[index]["text"].lower():
                        section_title_indices = levels[level][font]
                        info("line index of Reference section : " + str(index))
                        ref_start_index = index

                        ref_section_found = True
                        break
                if ref_section_found:
                    break
            if ref_section_found:
                break

        for i in section_title_indices:
            node_data = {"text": paper.x_lines[i]["text"].strip(), "index": i}
            paper.sections.append(node_data)

        if len(section_title_indices) < 3 or len(section_title_indices) > 15:
            paper.warnings.append("[WARNING] number of sections")

        #paper = self.extractReferences(paper, ref_start_index)

        return paper

    def extractReferences(self, paper, start_index):
        i = start_index
        line_index = 0
        ref_id = 1
        refs = []
        ref_tree_index = 0
        end_index = len(paper.x_lines)
        if len(paper.sections) == 0:
            paper.warnings.append("[WARNING] len(sections) = 0")
            end_index = min(start_index + 5, len(paper.x_lines))
        elif "reference" in paper.sections[-1]["text"].lower():
            info("References is the last section of the paper")
        else:
            # TODO:: backward iteration is obviously more efficient.
            for j in range(len(paper.sectionssections)):
                if "reference" in paper.sections[j]["text"].lower():
                    ref_tree_index = j

                    end_index = paper.sections[j + 1]["index"]
                    break

        info("References ends in " + str(end_index))

        while i != end_index:
            ref, i = self.extractReferenceEntry(paper, i,
                                                start_index, end_index, ref_id)

            ref_id = int(ref["tag"]) + 1

            paper.references[ref["tag"]] = ref["text"]
        return paper

    def extractReferenceEntryManually(self, text):
        ref = {"tag": "", "text": "", "view_tag": ""}

        if re.match(r"^\[.*\d+.*\]", text.strip()):
            ref["tag"] = text.strip()[text.find('[') + 1:text.find(']')]
            ref["text"] = text.strip()[text.find(']') + 1:]
        elif re.match(r"^\d+\.\s+", text.strip()):
            ref["tag"] = text.strip()[:text.find('.')]
            ref["text"] = text.strip()[text.find('.') + 1:]
        else:  # for citations that the tag is not included
            ref["tag"] = "-1"
            ref["text"] = text.strip()

        ref["view_tag"] = str(uuid.uuid4())
        ref["candidate_bib"] = self.referenceStringToBibtex(ref["text"])

        info("reference manually extracted: ")
        info(ref)

        return ref

    def extractReferenceEntry(self, paper, line_index,
                              section_start_index, section_end_index,
                              expected_ref_id):
        i = line_index

        ref = {"tag": "-1"}
        entry_text = ""

        next_entry_found = False

        ref_id = 0

        while i != section_end_index and not next_entry_found:

            line = paper.x_lines[i]["text"]

            if re.match(r"^\[\d+\]", line.strip()):
                ref_id = int(line.strip()[line.find('[') + 1:line.find(']')])
            elif re.match(r"^\d+\.\s+", line.strip()):
                ref_id = int(line.strip()[:line.find('.')])
            else:
                ref_id = 0

            if ref_id != 0:
                if ref_id == expected_ref_id:
                    # setting font size on first reference
                    # if expected_ref_id == 1 :
                    #    expected_font_size = data.
                    ref["tag"] = str(ref_id)
                    info("ref #" + ref["tag"] + " line= " + str(i))
                    entry_text = ""
                elif ref_id == expected_ref_id + 1:
                    # TODO:: check whether ref[tag] == ref_id
                    next_entry_found = True
                    break
                else:
                    info("suspicious line! line= " + str(i))

            entry_text += line

            i = i + 1

        ref["text"] = entry_text
        # print(ref)

        return ref, i

    def getReferenceYear(self, ref_string):
        year = "1900"
        matches = re.findall(r'([1-2][0-9]{3})', ref_string)

        if len(matches) > 0:
            for match in matches:
                if int(match) > 1900 and int(match) < 2100:
                    year = match
                    break
        return year

    def referenceStringToBibtex(self, ref_string):
        try:
            bib_dict = {}
            quo_split = re.split('"', ref_string)
            if len(quo_split) == 3:
                bib_dict["title"] = quo_split[1]
                bib_dict["year"] = self.getReferenceYear(quo_split[2])
                bib_dict["venue"] = quo_split[2]
                return bib_dict

            venue_keywords = ["journal", "conference", "proceeding", "workshop"]
            # Reference String must include a valid year

            ref_string = re.sub("-\n", "", ref_string)
            ref_string = re.sub("\n", " ", ref_string)
            find_dots = re.findall(r'[\w\)]{2,40}\.', ref_string)
            split_dots = re.split(r'[\w\)]{2,40}\.', ref_string)
            if len(find_dots) == 0:
                raise Exception("Not dot structure in the reference string")
            else:
                if len(find_dots) != len(split_dots):
                    if split_dots[0] == "":
                        split_dots = split_dots[1:]
                    else:
                        split_dots = split_dots[:len(find_dots)]

                i = 0
                for x, y in zip(split_dots, find_dots):
                    # each part must be classified
                    # into [title, year, venue, authors]
                    part = x + y
                    year = self.getReferenceYear(part)
                    if year != "1900":
                        if "year" not in bib_dict.keys():
                            bib_dict["year"] = year
                            bib_dict["year_index"] = i
                        else:
                            info("two valid years have been found in: ")
                            info(ref_string)

                    if i == 0:  # We are confident that it is authors part
                        if "year" in bib_dict.keys():
                            if part.find("(") != -1:
                                part = part[:part.find("(")]
                    elif i == 1:
                        # We are confident that it is article title
                        bib_dict["title"] = part.strip()
                    elif i > 1:
                        com_parts = part.split(", ")
                        for com_part in com_parts:
                            for word in venue_keywords:
                                venue_word_found = False
                                if word in com_part.lower():
                                    venue_word_found = True
                                    break
                            if venue_word_found:
                                bib_dict["venue"] = com_part.strip()
                    i = i + 1
                return bib_dict
        except Exception as e:
            return None

    def extractBow(self, paper): # Extracting BOW and NER from PDF parsed string
        try:
            section_bows = []
            info = []

            text = ""
            counter = 0
            for line in paper.x_lines:
                if "references" in line["text"].lower() and counter > 100:
                    break
                text = text + line["text"]
                counter = counter + 1


            # for axis in axes:
            #     axis["RATE"] = []


            text = re.sub(r'[\n\r\t]', ' ', text.strip())
            text = re.sub(r'-\s', '', text)

            text = re.sub(r'[^a-zA-Z0-9_ .]', ' ', text)
            text = re.sub(r'[\s]+', r' ', text)

            my_doc = self.nlp(text)
            token_list = []
            for token in my_doc:
                token_list.append(token.text)


            for word in token_list:
                lexeme = self.nlp.vocab[word]
                if lexeme.is_stop == False:
                    paper.bow.append(word) 
            
            report = {}
            report["clean_count"] = 0
            
            # for sent in digest.sents:
                
            #     verb_found = False
            #     for token in sent:
            #         if token.pos_ == "VERB" or token.pos_ == "AUX":
            #             verb_found = True
            #             break

            #     if verb_found and ( sent[-1].pos_ == "PUNCT" or sent[-1].pos_ == "SPACE"):
            #     #if "-" in sent[-1].text or (len(sent) > 1 and "-" in sent[-2].text):
            #         #pos = [ word.pos_ for word in sent ]
            #         #print(sent.text)
            #         #print(pos)
            #         #print("\n")
            #         # for axis in axes:
            #         #     axis["RATE"].append((sent, sent.similarity(axis["REF"])))            
            #         #sents.append(sent)
            #         report["clean_count"] += 1



            #     ref_found = False
            #     # find reference section
            #     for token in sent:
            #         if token.lower_ == "references" and len(sent)<=6:
            #             ref_found = True
            #             break

            #     if ref_found:
            #         break

            #     #strs = "how much for the maple syrup? $20.99? That's ricidulous!!!"
            #     #strs = re.sub(r'[?|$|.|!]',r'',strs) #for remove particular special char
            #     #strs = re.sub(r'[^a-zA-Z0-9 ]',r'',strs) #for remove all characters
            #     #strs=''.join(c if c not in map(str,range(0,10)) else '' for c in strs) #for remove numbers
            #     #strs = re.sub('  ',' ',strs) #for remove extra spaces
            #     #print(strs) 


            datasets = []
            report["eigen_vectors"] = []
            report["eigen_values"] = []
            # for axis in axes:
            #     temp = [y for (x,y) in axis["RATE"]]
            #     temp[:] = (temp[:] - min(temp)) / (max(temp) - min(temp))
            #     datasets.append(temp)

            #     # Generating report
            #     report["eigen_vectors"].append(axis["REF"].text.split(' ', 1)[0])
            #     report["eigen_values"].append(sum(datasets[-1])/len(datasets[-1]))

            #     sorted_by_second = sorted(axis["RATE"], key=lambda tup: abs(tup[1]),reverse = True)
            #     print("\n\n")
            #     print(axis["REF"].text.split(' ', 1)[0])
            #     count = 0
            #     for (sent,rate) in sorted_by_second:
            #         print("\n" + sent.text)
            #         print(rate)
            #         if count == 5:
            #             break
            #         else:
            #             count += 1

            #    print("\n"+ sent)




            #section_bows = prepare_paper_for_LDA(nlp, text)

            return paper
        except Exception as e:
            print(e)
            return paper