"""Train K-Means and optional labelled KNN on curated PostgreSQL garden features.

Requires scikit-learn, numpy, psycopg. No image classification without
visual feature extraction; no fabricated labels or synthetic examples.
"""
import argparse
import json
import os
from collections import Counter

FEATURES = ("lawn", "terrace", "pathway", "trees", "shrubs", "fence")
def vector(values):
    if not all(key in values and isinstance(values[key], bool) for key in FEATURES):
        return None
    return [float(values[key]) for key in FEATURES]

def run(conn, dataset_id, k=3, apply=False, label_type=None):
    from sklearn.cluster import KMeans
    from sklearn.neighbors import KNeighborsClassifier
    with conn.cursor() as cur:
        cur.execute("""SELECT d.status,i.item_id,i.split,f.feature_values,f.reviewed
                       FROM horticulture.ml_dataset_version d
                       JOIN horticulture.ml_dataset_item i ON i.dataset_id=d.dataset_id
                       LEFT JOIN horticulture.ml_garden_features f ON f.image_id=i.item_id
                       WHERE d.dataset_id=%s AND i.item_kind='GARDEN_IMAGE'
                       ORDER BY i.item_id""",(dataset_id,))
        rows = cur.fetchall()
    if not rows or any(r[0]!="FROZEN" for r in rows):
        raise ValueError("Dataset must exist and be frozen")
    usable = [(image_id,split,vector(features))
              for _,image_id,split,features,reviewed in rows
              if reviewed and isinstance(features,dict) and vector(features) is not None]
    train = [(i,x) for i,s,x in usable if s=="TRAIN"]
    if len(train)<k or k<2:
        raise ValueError(f"Insufficient reviewed TRAIN features: {len(train)} for k={k}")
    km = KMeans(n_clusters=k,random_state=42,n_init=10).fit([x for _,x in train])
    assignments = [(i,s,str(int(km.predict([x])[0]))) for i,s,x in usable]
    print(json.dumps({"dataset_id":dataset_id,"reviewed_features":len(usable),
                      "train_count":len(train),"kmeans_clusters":k,
                      "split_counts":dict(Counter(s for _,s,_ in usable)),
                      "assignments":assignments},ensure_ascii=False))
    knn_assignments = []
    if label_type:
        with conn.cursor() as cur:
            cur.execute("""SELECT l.image_id,l.label_value
                           FROM horticulture.ml_garden_label l
                           WHERE l.label_type=%s AND l.label_source IN ('HUMAN','EXPERT')""",
                        (label_type,))
            labels = dict(cur.fetchall())
        labelled_train = [(i,x,labels[i]) for i,x in train if i in labels]
        if len(labelled_train)<2 or len({v for _,_,v in labelled_train})<2:
            raise ValueError("KNN requires >=2 labelled TRAIN examples from >=2 classes")
        neighbours=min(3,len(labelled_train))
        knn=KNeighborsClassifier(n_neighbors=neighbours)
        knn.fit([x for _,x,_ in labelled_train],[v for _,_,v in labelled_train])
        knn_assignments=[(i,s,str(knn.predict([x])[0])) for i,s,x in usable]
        print(json.dumps({"knn_label_type":label_type,
                          "knn_train_labels":len(labelled_train),
                          "knn_assignments":knn_assignments},ensure_ascii=False))
    if apply:
        with conn.cursor() as cur:
            for image_id,split,label in assignments:
                cur.execute("""INSERT INTO horticulture.ml_classification_result
                  (dataset_id,item_kind,item_id,algorithm,model_version,predicted_label)
                  VALUES (%s,'GARDEN_IMAGE',%s,'KMEANS',%s,%s)
                  ON CONFLICT (dataset_id,item_kind,item_id,algorithm,model_version)
                  DO UPDATE SET predicted_label=EXCLUDED.predicted_label""",
                  (dataset_id,image_id,f"kmeans-k{k}-baseline",label))
            for image_id,split,label in knn_assignments:
                cur.execute("""INSERT INTO horticulture.ml_classification_result
                  (dataset_id,item_kind,item_id,algorithm,model_version,predicted_label)
                  VALUES (%s,'GARDEN_IMAGE',%s,'KNN',%s,%s)
                  ON CONFLICT (dataset_id,item_kind,item_id,algorithm,model_version)
                  DO UPDATE SET predicted_label=EXCLUDED.predicted_label""",
                  (dataset_id,image_id,f"knn-{label_type}-k{min(3,len(labelled_train))}-baseline",label))
        conn.commit()
    return assignments

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--dataset-id",type=int,required=True)
    parser.add_argument("--clusters",type=int,default=3)
    parser.add_argument("--apply",action="store_true")
    parser.add_argument("--label-type",help="Optional expert-labelled garden category for KNN")
    args=parser.parse_args()
    dsn=os.environ.get("GARDNAIZE_ML_DATABASE_URL")
    if not dsn:
        raise SystemExit("GARDNAIZE_ML_DATABASE_URL required")
    import psycopg
    with psycopg.connect(dsn) as conn:
        run(conn,args.dataset_id,args.clusters,args.apply,args.label_type)
if __name__=="__main__":
    main()
