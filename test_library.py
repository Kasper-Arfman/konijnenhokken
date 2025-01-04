import pickle

with open(r'C:\Users\arfma005\Documents\GitHub\konijnenhokken\library.pkl', 'rb') as f:
    lib = pickle.load(f)


d = {}

for k in sorted(lib):

    t, r1, r2, c = k

    stop, play = lib[k]

    if play > stop:
        d[r1, r2, c] = t



d = dict(sorted(d.items(), key=lambda x: -x[1]))

for k, v in d.items():
    print(k, v)


    

