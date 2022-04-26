
def prepare_bows():
    logger = util.xxLogger.getLogger()
    nlpWrapper = util.xxGlobals.getNlpWrapper()
    results = []
    try:
        cursor = Paper.objects()
        for paper in cursor:

            # removing all tokens that have less than 3 characters
            # for token in paper.raw.bow:
            #     paper.raw.bow[:] = [x for x in paper.raw.bow if len(x)>2]
            
            # fixing bi-grams manually from observations
            nbow = paper.raw.bow
            paper.raw.bow.clear()
            tp = ""
            for t in paper.raw.bow:
                if t != "public" and t!= "key":
                    paper.raw.bow.append(t)
                else:
                    if tp == "public" and t == "key":
                        paper.raw.bow.append("publickey")
                tp = t 
            print(paper.raw.bow)
            paper.save()

    except Exception as e:
        print(str(e))