from sklearn.datasets import make_blobs
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

import util.xxGlobals

class MlWrapper:

    def __init__(self):
        self.test = 1

    def runKmeans(self, features):
        logger = xxGlobals.getLogger()
        
        # normalization phase
        scaler = StandardScaler()
        scaled_features = scaler.fit_transform(features)
        
        kmeans = KMeans(
            init="random",
            n_clusters=3,
            n_init=10,
            max_iter=300,
            random_state=42
        )    

        kmeans.fit(scaled_features)
        #print(scaled_features)
        
        return kmeans.labels_
